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



"""
For eval_harnness q011

BM25 doesn't just rank clause "1" low — it's completely absent from BM25's top 15

hybrid regressed on this question because RRF's
additive design let two consistently-mediocre candidates outrank a 
single retriever's top-confidence answer" is a specific, correct, defensible 
diagnosis — far stronger than "hybrid seemed worse."
"""

if __name__ == "__main__":
    
    question_vec = embed_question("What is the separation date under this agreement?")
    kq = keyword_query("How can i get refund from foodpanda", 15, where={"doc_id" : "agreement-tesla-kirkhorn"})
    vq = vector_query(question_vec, 15, where={"doc_id" : "agreement-tesla-kirkhorn"})
    
    print("-------------------keyword search-------------------")
    print([{r["metadata"]["section_id"]} for r in kq])
    
    print("-------------------vector search-------------------")
    print([{r["metadata"]["section_id"]} for r in vq])
    
    
    rankFusion = reciprocal_rank_fusion(vq, kq)
    print("-------------------hybrid search-------------------")
    print([{r["metadata"]["section_id"]} for r in rankFusion])

    #print([{"chunk_id": r["chunk_id"], "score" : r["score"]} for r in rankFusion])
# def query():
