import json

from app.config import GOLDEN_SET_PATH, EVAL_RESULT_PATH
from app.embedding.embedder import embed_question
from app.retrieval.vector_store import query as vector_query
from app.eval.retrieval_eval import precision_at_k, recall_at_k, reciprocal_rank
from app.retrieval.keyword_store import query as keyword_query
from app.retrieval.hybrid import reciprocal_rank_fusion
from datetime import datetime

def evaluate(retriever, data, k=5):
    """Run an evaluator over the golden set. `retriever(d) -> list[dict]`"""
    rows = []
    totals = {"precision": 0.0, "recall": 0.0, "mrr": 0.0}

    for d in data:
        results = retriever(d)
        retrieved_ids = [r["metadata"]["section_id"] for r in results]
        expected = d["expected_section_ids"]

        p = precision_at_k(retrieved_ids, expected, k)
        r = recall_at_k(retrieved_ids, expected, k)
        mrr = reciprocal_rank(retrieved_ids, expected)

        totals["precision"] += p
        totals["recall"]    += r
        totals["mrr"]       += mrr

        rows.append({
            "id": d["id"],
            "precision": p,
            "recall": r,
            "mrr": mrr,
        })

    n = len(data) or 1
    means = {f"mean_{key}": val / n for key, val in totals.items()}
    return rows, means


# ---- Retriever definitions (each is a one-liner) ----

def naive_retriever(d, k=5):
    qv = embed_question(d["question"])
    return vector_query(qv, k, where={"doc_id": d["document_id"]})

def hybrid_retriever(d, k=5):
    qv = embed_question(d["question"])
    vec = vector_query(qv, k, where={"doc_id": d["document_id"]})
    kw  = keyword_query(d["question"], k, where={"doc_id": d["document_id"]})
    return reciprocal_rank_fusion(vec, kw, k)

# def rerank_retriever(d, k=5):
    # qv = embed_question(d["question"])
    # vec = vector_query(qv, candidates, where={"doc_id": d["document_id"]})
    # kw  = keyword_query(d["question"], candidates, where={"doc_id": d["document_id"]})
    # fused = reciprocal_rank_fusion(vec, kw, candidates)
    # return rerank(d["question"], fused, k)   # your final reranker


if __name__ == "__main__":
    data = json.loads(GOLDEN_SET_PATH.read_text())

    # output = []
    # query_k = 5
    # precision_k = 5

    # total_naive_precision, total_naive_recall, total_naive_reciprocal = 0,0,0
    # total_hybrid_precision, total_hybrid_recall, total_hybrid_reciprocal = 0,0,0
    
    # for d in data:
    #     question_vector = embed_question(d["question"])
    #     vecto_rquery_result = vector_query(question_vector, query_k, where={"doc_id" : d["document_id"]})
    #     naive_retrieved_ids = [q["metadata"]["section_id"] for q in vecto_rquery_result]

    #     # ------------------------NAIVE------------------------

    #     naive_precision = precision_at_k(naive_retrieved_ids, d["expected_section_ids"], precision_k)
    #     naive_recall = recall_at_k(naive_retrieved_ids, d["expected_section_ids"], precision_k)
    #     naive_reciprocal = reciprocal_rank(naive_retrieved_ids, d["expected_section_ids"])

    #     total_naive_precision += naive_precision
    #     total_naive_recall += naive_recall
    #     total_naive_reciprocal += naive_reciprocal

    #     # ------------------------Hybrid------------------------
    #     keyword_query_result = keyword_query("How can i get refund from foodpanda", query_k, where={"doc_id" : d["document_id"]})

    #     hybrid_result = reciprocal_rank_fusion(vecto_rquery_result, keyword_query_result,query_k)

    #     hybrid_retrieved_ids = [q["metadata"]["section_id"] for q in vecto_rquery_result]
        
    #     hybrid_precision = precision_at_k(hybrid_retrieved_ids, d["expected_section_ids"], precision_k)
    #     hybrid_recall = recall_at_k(hybrid_retrieved_ids, d["expected_section_ids"], precision_k)
    #     hybrid_reciprocal = reciprocal_rank(hybrid_retrieved_ids, d["expected_section_ids"])

    #     # ------------------------Append------------------------
    #     output.append({"id" : d["id"], 
    #                    "naive_precision" : naive_precision, 
    #                    "naive_recall" : naive_recall, 
    #                    "naive_reciprocal":naive_reciprocal,
    #                    "hybrid_precision" : hybrid_precision, 
    #                     "hybrid_recall" : hybrid_recall, 
    #                     "hybrid_reciprocal":hybrid_reciprocal
    #                    })

    # # ------------------------NAIVE MEAN------------------------
    
    # naive_mean_precision = total_naive_precision / len(data)  
    # naive_mean_recall = total_naive_recall / len(data)
    # naive_mean_reciprocal = total_naive_reciprocal / len(data)

    # # ------------------------HYBRID MEAN------------------------
        

    # now = datetime.now()
    # with open(EVAL_RESULT_PATH, "w", encoding="utf-8") as f:
    #     json.dump({"Date": now.strftime("%m/%d/%Y"), 
    #                "Time": now.strftime("%I:%M:%S %p"),
    #                "naive_mean_precision" : naive_mean_precision,
    #                "naive_mean_recall" : naive_mean_recall,
    #                "naive_mean_reciprocal" : naive_mean_reciprocal, 
    #                "Data Process" : output }, f, ensure_ascii=False)

    strategies = {
        "naive":  naive_retriever,
        "hybrid": hybrid_retriever,
        # "rerank": rerank_retriever,   # uncomment when ready
    }

    report = {"Date": datetime.now().strftime("%m/%d/%Y"),
              "Time": datetime.now().strftime("%I:%M:%S %p")}

    for name, retriever in strategies.items():
        rows, means = evaluate(retriever, data, k=5)
        report[name] = {"means": means, "rows": rows}

    with open(EVAL_RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
