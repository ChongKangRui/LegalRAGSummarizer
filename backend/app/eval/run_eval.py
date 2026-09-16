import json

from app.config import GOLDEN_SET_PATH, EVAL_RESULT_PATH
from app.embedding.embedder import embed_question
from app.retrieval.vector_store import query as vector_query
from app.eval.retrieval_eval import precision_at_k, recall_at_k, reciprocal_rank
from app.retrieval.keyword_store import query as keyword_query
from app.retrieval.hybrid import reciprocal_rank_fusion
from app.retrieval.reranker import rerank
from app.generation.llm_client import answer
from app.generation.citation_validator import get_citation, citation_validity, citation_correctness
from datetime import datetime

def evaluate(retriever, data, k=5):
    """Run an evaluator over the golden set. `retriever(d) -> list[dict]`"""
    rows = []
    totals = {"precision": 0.0, "recall": 0.0, "rr": 0.0, "cv" : 0, "cc" : 0}
    no_citation_count = 0
    generation_failed_count = 0
    citation_measured_count = 0
    for d in data:
        results = retriever(d, k)
        retrieved_ids = [r["metadata"]["section_id"] for r in results]
        expected = d["expected_section_ids"]

        p = precision_at_k(retrieved_ids, expected, k)
        r = recall_at_k(retrieved_ids, expected, k)
        rr = reciprocal_rank(retrieved_ids, expected)

        totals["precision"] += p
        totals["recall"]    += r
        totals["rr"]       += rr

        try:
            outcome = answer(d["question"],results, "openai/gpt-oss-120b")
            citations = get_citation(outcome, results, False)
            print(f"[{d['id']}] generation success")
        except Exception as e:
            outcome, citations = None, []
            generation_failed_count+=1
            print(f"[{d['id']}] generation failed after retries: {e}")
            v, c = None, None
        else:
            v = citation_validity(citations)
            c = citation_correctness(citations, expected)
            if v is None:
                no_citation_count += 1
            else:
                citation_measured_count+=1
                totals["cv"] += v
                totals["cc"] += c

        rows.append({
            "id": d["id"],
            "precision": p,
            "recall": r,
            "rr": rr,
            "cv" : v,
            "cc" : c,
            "retrieved_ids" : retrieved_ids,
            "answer" : outcome
        })

    n = len(data) or 1
    means = {
    "mean_precision": totals["precision"] / n,
    "mean_recall": totals["recall"] / n,
    "mean_rr": totals["rr"] / n,
    "mean_cv": totals["cv"] / citation_measured_count if citation_measured_count else None,
    "mean_cc": totals["cc"] / citation_measured_count if citation_measured_count else None,
    "no_citation_count": no_citation_count,
    "generation_failed_count": generation_failed_count,
    }
    return rows, means


# ---- Retriever definitions (each is a one-liner) ----

def vector_retriever(d, k=5):
    qv = embed_question(d["question"])
    return vector_query(qv, k, where={"doc_id": d["document_id"]})

def hybrid_retriever(d, k=5, candidate_k=None):
    candidate_k = candidate_k or max(k * 3, 15)
    qv = embed_question(d["question"])
    vec = vector_query(qv, candidate_k, where={"doc_id": d["document_id"]})
    kw  = keyword_query(d["question"], candidate_k, where={"doc_id": d["document_id"]})
    return reciprocal_rank_fusion(vec, kw)[:k]

def rerank_retriever(d, k=5, candidate_k=15):
    hybrid_res = hybrid_retriever(d, candidate_k=candidate_k)
    return rerank(d["question"], hybrid_res, k) 


if __name__ == "__main__":
    data = json.loads(GOLDEN_SET_PATH.read_text())

    k = 2

    strategies = {
        "vector":  vector_retriever,
        "hybrid": hybrid_retriever,
        "hybrid_rerank": rerank_retriever,   
    }
    now = datetime.now()
    iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    report = {"Date": iso,
                "k" : k
              }

    for name, retriever in strategies.items():
        rows, means = evaluate(retriever, data, k)
        report[name] = {"means": means, "rows": rows}

    with open(EVAL_RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
