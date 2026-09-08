from one_naive_baseline import DOCUMENT, naive_chunk

# from sentence_transformers import SentenceTransformer
# model = SentenceTransformer("BAAI/bge-small-en-v1.5")

from fastembed import TextEmbedding
import numpy as np
model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5") 

def retrieve(question: str, chunks: list[str], top_k: int = 3)->list[str]:
    """Naive vector retrieval: return the top_k most similar fixed-size chunks."""

    # chunk_vectors = model.encode(chunks)
    # question_vector = model.encode(question)

   

    chunk_vectors = np.array(list(model.embed(chunks)))
    question_vector = next(iter(model.query_embed(question)))

    # print("ChunkV=",chunk_vectors)
    # print("questionV=",question_vector)

    scores = chunk_vectors @ question_vector
    ranked = scores.argsort()[::-1]
    return [chunks[i] for i in ranked[:top_k]]

if __name__ == "__main__":
    question = "How much time does licensee have to pay an invoice?"
    for rank, chunk in enumerate(retrieve(question, naive_chunk(DOCUMENT), 1), start=1):
        print(f"#{rank}\n{chunk}\n")