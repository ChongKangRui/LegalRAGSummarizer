from fastembed.rerank.cross_encoder import TextCrossEncoder
from functools import cache


from app.retrieval.keyword_store import query as keyword_query
from app.retrieval.numpy_store import query as vector_query
from app.embedding.embedder import embed_question
from app.retrieval.hybrid import reciprocal_rank_fusion

import threading
_lock = threading.Lock()

@cache
def get_reranker():
    with _lock:
        return TextCrossEncoder("Xenova/ms-marco-MiniLM-L-6-v2")


def rerank(query: str, hits: list[dict], top_k: int = 5):
    reranker = get_reranker()
    docs = [h["text"] for h in hits]  
    scores = list(reranker.rerank(query, docs))

    ranked = sorted(zip(hits, scores), key=lambda x: x[1], reverse=True)
    return [{**hit, "score": score} for hit, score in ranked[:top_k]]

if __name__ == "__main__":
    kq = keyword_query("How can i get refund from foodpanda", 5, where={"doc_id" : "tos-foodpanda"})
    question_vec = embed_question("How can i get refund from foodpanda")
    vq = vector_query(question_vec, 5, where={"doc_id" : "tos-foodpanda"})
    rankFusion = reciprocal_rank_fusion(vq, kq, 5)
    print("---------------hybrid result------------------")
    print([{"chunk_id": r["chunk_id"], "score" : r["score"]} for r in rankFusion])

    print("---------------rerank result------------------")
    rerank_result = rerank("How can i get refund from foodpanda", rankFusion, 5)
    print([{"chunk_id": r["chunk_id"], "score" : r["score"]} for r in rerank_result])
    
   
