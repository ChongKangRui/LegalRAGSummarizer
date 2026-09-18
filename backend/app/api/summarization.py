from fastapi import APIRouter, HTTPException
from pydantic import Field
from dataclasses import dataclass

from app.models import CamelModel, Strategy, ALL_STRATEGIES, LARGE_ONLY_VALUES

from app.retrieval.vector_store import query as vector_query, get_chunks
from app.retrieval.keyword_store import query as keyword_query
from app.retrieval.hybrid import reciprocal_rank_fusion
from app.retrieval.reranker import rerank
from app.embedding.embedder import embed_question
from app.generation.llm_client import answer, answer_with_stream, summarize_context_map_reducer, summarize_context_refine

from app.generation.citation_validator import get_citation, CitationResponse
from app.retrieval.truncate_and_stuff import truncate_and_stuff
from app.retrieval.map_reducer import map_reducer



from fastapi.responses import StreamingResponse

import asyncio
import json
import time

from app.config import ENABLE_LARGE_ANSWER_STRATEGY

router = APIRouter(prefix="/summarize", tags=["summarize"])

def sse(obj): return f"data: {json.dumps(obj)}\n\n"

class QueryRequest(CamelModel):
    document_id: str = Field(alias="documentId")
    query: str
    strategy: str

class SummaryResponse(CamelModel):
    document_id: str
    query: str
    answer: str
    citations: list[CitationResponse]
    strategy: str
    latency_ms: float
    
    

    
class StrategyResponse(CamelModel):
    strategies : list[Strategy]
    


    
    
    
@dataclass
class QueryResult:
    """Everything the event stream needs to produce an answer + citations."""
    query: str
    document_id: str
    strategy: str
    hits: list
    chunks: list
    refine_result: str | None = None   # precomputed answer for "refine"





# ---------------------------------------------------------------------------
# Strategy dispatch
# ---------------------------------------------------------------------------

def _require_large_answer_strategy() -> None:
    if not ENABLE_LARGE_ANSWER_STRATEGY:
        raise HTTPException(
            status_code=503,
            detail="Large answer strategy is disabled on this server.",
        )


async def _run_naive(body: QueryRequest) -> QueryResult:
    _require_large_answer_strategy()
    chunks = get_chunks(body.document_id)
    hits = truncate_and_stuff(chunks)
    return QueryResult(body.query, body.document_id, body.strategy, hits, chunks)


async def _run_map_reduce(body: QueryRequest) -> QueryResult:
    _require_large_answer_strategy()
    chunks = get_chunks(body.document_id)
    groups = map_reducer(chunks)
    tasks = [summarize_context_map_reducer(body.query, g) for g in groups]
    hits = await asyncio.gather(*tasks)
    return QueryResult(body.query, body.document_id, body.strategy, hits, chunks)


async def _run_refine(body: QueryRequest) -> QueryResult:
    _require_large_answer_strategy()
    chunks = get_chunks(body.document_id)
    groups = map_reducer(chunks)

    summarization = ""
    for group in groups:
        summarization = await summarize_context_refine(body.query, summarization, group)

    return QueryResult(body.query, body.document_id, body.strategy, hits=[], chunks=chunks,
                       refine_result=summarization)


async def _run_vector(body: QueryRequest, question_vec, top_k: int) -> QueryResult:
    hits = await asyncio.to_thread(
        vector_query, question_vec, top_k,
        where={"doc_id": body.document_id},
    )
    return QueryResult(body.query, body.document_id, body.strategy, hits, chunks=[])


async def _run_hybrid(body: QueryRequest, question_vec, top_k: int) -> QueryResult:
    v, kw = await asyncio.gather(
        asyncio.to_thread(vector_query, question_vec, top_k,
                          where={"doc_id": body.document_id}),
        asyncio.to_thread(keyword_query, body.query, top_k,
                          where={"doc_id": body.document_id}),
    )
    hits = reciprocal_rank_fusion(v, kw)[:top_k]
    return QueryResult(body.query, body.document_id, body.strategy, hits, chunks=[])


async def _run_hybrid_rerank(body: QueryRequest, question_vec, top_k: int) -> QueryResult:
    v, kw = await asyncio.gather(
        asyncio.to_thread(vector_query, question_vec, top_k,
                          where={"doc_id": body.document_id}),
        asyncio.to_thread(keyword_query, body.query, top_k,
                          where={"doc_id": body.document_id}),
    )
    hybrid_res = reciprocal_rank_fusion(v, kw)[:top_k]
    hits = await asyncio.to_thread(rerank, body.query, hybrid_res, top_k)
    return QueryResult(body.query, body.document_id, body.strategy, hits, chunks=[])


# ---------------------------------------------------------------------------
# Entry point: resolve strategy -> QueryResult
# ---------------------------------------------------------------------------

async def compute_query_result(body: QueryRequest, top_k: int = 5) -> QueryResult:
    question_vec = embed_question(body.query)

    match body.strategy:
        case "naive":
            return await _run_naive(body)
        case "map_reduce":
            return await _run_map_reduce(body)
        case "refine":
            return await _run_refine(body)
        case "vector":
            return await _run_vector(body, question_vec, top_k)
        case "hybrid":
            return await _run_hybrid(body, question_vec, top_k)
        case "hybrid_rerank":
            return await _run_hybrid_rerank(body, question_vec, top_k)
        case _:
            raise HTTPException(status_code=400, detail=f"Unknown strategy: {body.strategy}")


# ---------------------------------------------------------------------------
# SSE stream
# ---------------------------------------------------------------------------

def make_event_stream(result: QueryResult, start: float):
    async def event_stream():
        text = ""

        if result.strategy == "refine":
            text = result.refine_result or ""
            yield sse({"type": "token", "text": text})
        else:
            async for piece in answer_with_stream(result.query, result.hits, result.strategy):
                text += piece
                yield sse({"type": "token", "text": piece})

        citation_source = (
            result.chunks if result.strategy in ("map_reduce", "refine") else result.hits
        )
        citations = get_citation(text, citation_source)

        yield sse({
            "type": "done",
            "documentId": result.document_id,        
            "strategy": result.strategy or "rerank",
            "citations": [c.model_dump(by_alias=True) for c in citations],
            "latencyMs": (time.perf_counter() - start) * 1000,
        })

    return event_stream


@router.post("/stream")
async def run_query_stream(body: QueryRequest):
    
    start = time.perf_counter()
    result = await compute_query_result(body)
    stream = make_event_stream(result, start)
    return StreamingResponse(stream(), media_type="text/event-stream")



# @router.post("/comparison")
# async def run_query_comparison(body: QueryRequest):
    
    

#     start = time.perf_counter()
#     result = await compute_query_result(body)
#     stream = make_event_stream(result, start)
#     return StreamingResponse(stream(), media_type="text/event-stream")

@router.get("/strategies", response_model=StrategyResponse)
def get_strategies() -> StrategyResponse:
    strategies = (
        ALL_STRATEGIES
        if ENABLE_LARGE_ANSWER_STRATEGY
        else [s for s in ALL_STRATEGIES if s.value not in LARGE_ONLY_VALUES]
    )
    return StrategyResponse(strategies=strategies)
    