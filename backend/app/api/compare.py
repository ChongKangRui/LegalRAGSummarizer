from typing import List

from pydantic import BaseModel, Field

# Import your existing types — adjust paths to match your project layout
from app.api.summarization import Strategy, compute_query_result, QueryRequest, QueryResult
from app.generation.citation_validator import get_citation, CitationResponse
from app.models import CamelModel, Strategy, ALL_STRATEGIES
from app.generation.llm_client import answer

from fastapi import APIRouter

import asyncio
import time

router = APIRouter(prefix="/compare", tags=["compare"])


class CompareRequest(CamelModel):
    document_id: str 
    query: str 
    strategies: List[str]


class CompareResult(CamelModel):
    strategy: str
    answer: str
    citations: List[CitationResponse]
    latency_ms: float
    

@router.post("", response_model=list[CompareResult])
async def run_compare(body: CompareRequest):
    
    start = time.perf_counter()
    
    query_results = await asyncio.gather(*(
        compute_query_result(QueryRequest(document_id=body.document_id, query=body.query, strategy=s))
        for s in body.strategies
    ))
    
    answers = await asyncio.gather(*(answer(body.query, q.hits) for q in query_results))

    
    results = []
    for s, q, a in zip(body.strategies, query_results, answers):
        citations = get_citation(a, q.hits)
        results.append(CompareResult(
            strategy=s,
            answer=a,
            citations=citations,
            latency_ms=(time.perf_counter() - start) * 1000,
        ))

    return results

    