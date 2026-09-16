from app.retrieval.keyword_store import query as keyword_query
from app.retrieval.numpy_store import query as vector_query
from app.embedding.embedder import embed_question



def reciprocal_rank_fusion(vector_hits : list[dict], keyword_hits : list[dict], k: int = 60):

   
    scores = {}
    chunks_by_id = {}

    for rank, hit in enumerate(vector_hits, start=1):
        chunk_id = hit["chunk_id"]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank)
        chunks_by_id[chunk_id] = hit

    for rank, hit in enumerate(keyword_hits, start=1):
        chunk_id = hit["chunk_id"]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank)
        chunks_by_id[chunk_id] = hit

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    return [{**chunks_by_id[score[0]], "score": score[1]} for score in sorted_scores]




if __name__ == "__main__":
    kq = keyword_query("How can i get refund from foodpanda", 5, where={"doc_id" : "tos-foodpanda"})
    question_vec = embed_question("How can i get refund from foodpanda")
    vq = vector_query(question_vec, 5, where={"doc_id" : "tos-foodpanda"})
    rankFusion = reciprocal_rank_fusion(vq, kq)

    print([{"chunk_id": r["chunk_id"], "score" : r["score"]} for r in rankFusion])
# def query():
