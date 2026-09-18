from fastapi import APIRouter, HTTPException
from pydantic import Field

from app.models import CamelModel

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


@router.post("/stream")
async def run_query_stream(body: QueryRequest):

    start = time.perf_counter()
    hits = []
    chunks = []
    refine_result = None  # only set when strategy == "refine"

    top_k = 5
    query = body.query
    question_vec = embed_question(query)

    match body.strategy:
        case "naive":
            if ENABLE_LARGE_ANSWER_STRATEGY is False:
                raise HTTPException(status_code=503, detail="Large answer strategy is disabled on this server.")
            chunks = get_chunks(body.document_id)
            hits = truncate_and_stuff(chunks)

        case "map_reduce":
            if ENABLE_LARGE_ANSWER_STRATEGY is False:
                raise HTTPException(status_code=503, detail="Large answer strategy is disabled on this server.")
            chunks = get_chunks(body.document_id)
            map_reduce_hits = map_reducer(chunks)
            tasks = [summarize_context_map_reducer(query, m) for m in map_reduce_hits]
            hits = await asyncio.gather(*tasks)

        case "refine":
            if ENABLE_LARGE_ANSWER_STRATEGY is False:
                raise HTTPException(status_code=503, detail="Large answer strategy is disabled on this server.")
            chunks = get_chunks(body.document_id)
            refine_groups = map_reducer(chunks)

            summarization = ""
            for group in refine_groups:
                summarization = await summarize_context_refine(query,summarization, group)

            refine_result = summarization  

        case "vector":
            hits = await asyncio.to_thread(vector_query, question_vec, top_k, where={"doc_id": body.document_id})
        case "hybrid":
            v = await asyncio.to_thread(vector_query, question_vec, top_k, where={"doc_id": body.document_id})
            kw = await asyncio.to_thread(keyword_query, query, top_k, where={"doc_id": body.document_id})
            hits = reciprocal_rank_fusion(v, kw)[:top_k]
        case "hybrid_rerank":
            v = await asyncio.to_thread(vector_query, question_vec, top_k, where={"doc_id": body.document_id})
            kw = await asyncio.to_thread(keyword_query, query, top_k, where={"doc_id": body.document_id})
            hybrid_res = reciprocal_rank_fusion(v, kw)[:top_k]
            hits = await asyncio.to_thread(rerank, query, hybrid_res, top_k)

    async def event_stream():
        text = ""

        if body.strategy == "refine":
            # already fully computed — nothing left to generate, just deliver it
            text = refine_result
            yield sse({"type": "token", "text": text})
        else:
            async for piece in answer_with_stream(query, hits, body.strategy):
                text += piece
                yield sse({"type": "token", "text": piece})

        citation_source = chunks if body.strategy in ("map_reduce", "refine") else hits
        citations = get_citation(text, citation_source)

        yield sse({
            "type": "done",
            "documentId": body.document_id,
            "strategy": body.strategy or "naive",
            "citations": [c.model_dump(by_alias=True) for c in citations],
            "latencyMs": (time.perf_counter() - start) * 1000,
        })

    return StreamingResponse(event_stream(), media_type="text/event-stream")