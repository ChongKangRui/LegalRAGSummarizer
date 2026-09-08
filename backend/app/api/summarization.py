from fastapi import APIRouter
from pydantic import BaseModel, Field, ConfigDict
from pydantic.alias_generators import to_camel

from app.retrieval.vector_store import query
from app.embedding.embedder import embed_question
from app.generation.llm_client import answer, answer_with_stream

from fastapi.responses import StreamingResponse

import time


# Like `const router = express.Router()` + every path in here is prefixed with /query
router = APIRouter(prefix="/summarize", tags=["summarize"])


# ---- Request / response bodies. FastAPI validates + documents these for you ----
class QueryRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    document_id : str = Field(alias="documentId")
    query: str
    strategy: str


class SummaryResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel,populate_by_name=True)
    document_id: str
    query: str
    answer: str
    citations: list[str]
    strategy:str
    latency_ms: float


# Attach the dependency in the decorator when the handler doesn't need its return value.
# (Alternative: `async def run_query(body, key: str = Depends(require_api_key))` to use it.)
@router.post("/", response_model=SummaryResponse)
async def run_query(body: QueryRequest):
    # `body` is already parsed + validated against QueryRequest.
    
    start = time.perf_counter()
    
    question_vec = embed_question(body.query)
    query_result = query(question_vec, 3, where={"doc_id" : body.document_id})

    answer_outcome = answer(body.query, query_result["documents"])
  
    print("Latency:", (time.perf_counter() - start) * 1000)
    return SummaryResponse(
        document_id=body.document_id,      # echo
        query=body.query,                  # echo
        answer=answer_outcome,                # real
        citations=[],                      # stub — Phase 3
        strategy=body.strategy or "naive", # stub — Phase 5
        latency_ms=(time.perf_counter() - start) * 1000,  # measured
    )

@router.post("/stream", response_model=StreamingResponse)
async def run_query_stream(body: QueryRequest)->StreamingResponse:
    # `body` is already parsed + validated against QueryRequest.
    
    start = time.perf_counter()
    
    question_vec = embed_question(body.query)
    query_result = query(question_vec, 3, where={"doc_id" : body.document_id})

   #answer_outcome = answer(body.query, query_result["documents"])
  
    print("Latency:", (time.perf_counter() - start) * 1000)
    return StreamingResponse(answer_with_stream(body.query, query_result["documents"]), media_type="text/plain")