from fastapi import APIRouter, HTTPException
from pydantic import Field

from app.models import CamelModel

from app.retrieval.vector_store import query as vector_query, get_chunks
from app.retrieval.keyword_store import query as keyword_query
from app.retrieval.hybrid import reciprocal_rank_fusion
from app.retrieval.reranker import rerank
from app.embedding.embedder import embed_question
from app.generation.llm_client import answer, answer_with_stream, summarize_context

from app.generation.citation_validator import get_citation, CitationResponse
from app.retrieval.truncate_and_stuff import truncate_and_stuff
from app.retrieval.map_reducer import map_reducer

from fastapi.responses import StreamingResponse

import asyncio

import json

import time

from app.config import ENABLE_LARGE_ANSWER_STRATEGY


# Like `const router = express.Router()` + every path in here is prefixed with /query
router = APIRouter(prefix="/summarize", tags=["summarize"])

def sse(obj): return f"data: {json.dumps(obj)}\n\n"

# ---- Request / response bodies. FastAPI validates + documents these for you ----
class QueryRequest(CamelModel):
    
    document_id : str = Field(alias="documentId")
    query: str
    strategy: str


class SummaryResponse(CamelModel):
    
    document_id: str
    query: str
    answer: str
    citations: list[CitationResponse]
    strategy:str
    latency_ms: float


# Attach the dependency in the decorator when the handler doesn't need its return value.
# (Alternative: `async def run_query(body, key: str = Depends(require_api_key))` to use it.)
# update: technically this route was abandone as stream 
#         will be the primary way for frontend to receive answer
@router.post("/", response_model=SummaryResponse)
def run_query(body: QueryRequest):
    
    start = time.perf_counter()

    question_vec = embed_question(body.query)

    vec = vector_query(question_vec, 5, where={"doc_id" : body.document_id})
    kw  = keyword_query(body.query, 5, where={"doc_id" : body.document_id})

    hybrid_result = reciprocal_rank_fusion(vec, kw)

    hits = rerank(body.query, hybrid_result, 5) 

    answer_outcome = answer(body.query, hits)


    print("Latency:", (time.perf_counter() - start) * 1000)
    return SummaryResponse(
        document_id=body.document_id,   
        query=body.query,               
        answer=answer_outcome,               
        citations=get_citation(answer_outcome, hits),                      # stub — Phase 3
        strategy=body.strategy,
        latency_ms=(time.perf_counter() - start) * 1000,  # measured
    )

@router.post("/stream")
async def run_query_stream(body: QueryRequest):
    
    start = time.perf_counter()
    hits = []
    chunks = []
    
    top_k = 5
    question_vec = embed_question(body.query)
    print(body.strategy)
    
    
    match(body.strategy):
        # naive will make as an bad example here
        case "naive":
            if ENABLE_LARGE_ANSWER_STRATEGY is False:
                raise HTTPException(
                status_code=503,
                detail="Large answer strategy is disabled on this server.",
            )
            chunks = get_chunks(body.document_id)
            hits = truncate_and_stuff(chunks)
        case "map_reduce":
            if ENABLE_LARGE_ANSWER_STRATEGY is False:
                           raise HTTPException(
                           status_code=503,
                           detail="Large answer strategy is disabled on this server.",
                       )
            chunks = get_chunks(body.document_id)
            map_reduce_hits = map_reducer(chunks)
            tasks = [summarize_context(body.query,m) for m in map_reduce_hits]
            hits = await asyncio.gather(*tasks)

        case "refine":
            if ENABLE_LARGE_ANSWER_STRATEGY is False:
                           raise HTTPException(
                           status_code=503,
                           detail="Large answer strategy is disabled on this server.",
                       )
            chunks = get_chunks(body.document_id)
            hits = truncate_and_stuff(chunks)
        case "vector":
            hits = await asyncio.to_thread(vector_query, question_vec, top_k, where={"doc_id": body.document_id})
        case "hybrid":
            v = await asyncio.to_thread(vector_query, question_vec, top_k, where={"doc_id": body.document_id})
            kw = await asyncio.to_thread(keyword_query, body.query, top_k, where={"doc_id": body.document_id})
            hits = reciprocal_rank_fusion(v, kw)[:top_k]
        case "hybrid_rerank":
            v = await asyncio.to_thread(vector_query, question_vec, top_k, where={"doc_id": body.document_id})
            kw = await asyncio.to_thread(keyword_query, body.query, top_k, where={"doc_id": body.document_id})
            hybrid_res = reciprocal_rank_fusion(v, kw)[:top_k]
            hits = await asyncio.to_thread(rerank, body.query, hybrid_res, top_k)
    
    #hits = vector_query(question_vec, 3, where={"doc_id" : body.document_id})

    async def event_stream():

        text = ""
        async for piece in answer_with_stream(body.query, hits, body.strategy):
            text += piece
    
            yield sse({"type":"token", "text" : piece})

        citations = get_citation(text, chunks if body.strategy == "map_reduce" else hits)
        
        yield sse({"type": "done", "documentId": body.document_id,
            "strategy": body.strategy or "naive",
            "citations": [c.model_dump(by_alias=True) for c in citations],
            "latencyMs": (time.perf_counter() - start) * 1000,})
  
    return StreamingResponse(event_stream(), media_type="text/event-stream")