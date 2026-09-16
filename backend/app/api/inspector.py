from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter
from pydantic.alias_generators import to_camel
from app.eval.run_eval import hybrid_retriever, vector_retriever, rerank_retriever

from app.models import CamelModel

router = APIRouter(prefix="/inspector", tags=["inspector"])

class Chunk(CamelModel):
    id: str
    document_id: str
    section_id: str
    clause_id: str
    heading: str
    text: str

class RetrievalRequest(CamelModel):
    document_id: str
    query: str

class RetrievalScore(CamelModel):
    chunk_id: str
    vector_score: float
    bm25_score: float
    rerank_score: float
    fused_rank: float



class RetrievelResult(CamelModel):
    document_id: str
    query: str
    chunks: list[Chunk]
    scores: list[RetrievalScore]
    
    
#"document_id": "tos-atlassian",
#"question": "Which law governs the agreement if the customer is based in Europe?",

@router.post("", response_model=RetrievelResult)
async def get_retrieval(request: RetrievalRequest):
    
    query = {"document_id" : request.document_id, "question": request.query}
    
    