from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter
from pydantic.alias_generators import to_camel

from app.embedding.embedder import embed_question
from app.retrieval.vector_store import query as vector_query
from app.retrieval.keyword_store import query as keyword_query
from app.retrieval.hybrid import reciprocal_rank_fusion
from app.retrieval.reranker import rerank

from app.models import CamelModel

router = APIRouter(prefix="/inspector", tags=["inspector"])

class Chunk(CamelModel):
    id: str
    document_id: str
    section_id: str
    text: str

class RetrievalRequest(CamelModel):
    document_id: str
    query: str

class RetrievalScore(CamelModel):
    chunk_id: str
    vector_score: float | None = None
    bm25_score: float | None = None
    rerank_score: float
    fused_rank : int


class RetrievelResult(CamelModel):
    document_id: str
    query: str
    chunks: list[Chunk]
    scores: list[RetrievalScore]
    
    

@router.post("", response_model=RetrievelResult)
async def inspector_result(request: RetrievalRequest):
    
    candidate_k = 15
    top_k = 10
    
    qv = embed_question(request.query)
    vector_result = vector_query(qv, candidate_k, where={"doc_id": request.document_id})
    keyword_result  = keyword_query(request.query, candidate_k, where={"doc_id":request.document_id})

    # defaults object structure
    # {"chunk_id": str, "text": str,
    # "score": float "metadata": {"doc_id":…, "section_id":…}}.

    merged = {}
    
    for vr in vector_result:
        cid = vr["chunk_id"]
        merged[cid] = {**vr, "vector_score" : vr["score"], "bm25_score" : None}
        
    for kr in keyword_result:
        cid = kr["chunk_id"]
        if cid in merged:
             merged[cid]["bm25_score"] = kr["score"]
        else:
            merged[cid] = {**kr, "vector_score" : None, "bm25_score" : kr["score"]}
    
    rerank_result = rerank(request.query, merged.values(), top_k)
    for m in rerank_result:
        print({**m, "text" : ""})
    
    
    chunks = [Chunk(id = r["chunk_id"],document_id=request.document_id, section_id=r["metadata"]["section_id"], text=r["text"]) for r in rerank_result]
    scores = [RetrievalScore(chunk_id = r["chunk_id"], vector_score=r["vector_score"], bm25_score=r["bm25_score"],rerank_score=r["score"], fused_rank=i+1 ) for i, r in enumerate(rerank_result)]
        
    
    return RetrievelResult(document_id=request.document_id, query=request.query, chunks=chunks, scores=scores)
    
    