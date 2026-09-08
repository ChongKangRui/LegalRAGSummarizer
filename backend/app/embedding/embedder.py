from fastembed import TextEmbedding
#import numpy as np
from functools import cache

@cache
def get_embedder() -> TextEmbedding:
    return TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

def embed_documents(chunks: list[str])->list[list[float]]:
    chunk_vectors = get_embedder().embed(chunks)
    """Embed chunk texts for storage. Uses passage-side encoding."""
    return [ v.tolist() for v in chunk_vectors]

def embed_question(question: str)->list[list[float]]:
    """Embed a user question for search. Uses query-side encoding (BGE prefix)."""
   
    question_vector = next(iter(get_embedder().query_embed(question)))

    return question_vector.tolist()

if __name__ == "__main__":
    
    from app.ingestion.loader import loadDocument
    from app.ingestion.chunker import structural_chunk
    
    doc = loadDocument()[0]
    chunks = structural_chunk(doc["text"], doc["doc_id"])
    #print(chunks)
    vecs = embed_documents([c["text"] for c in chunks])

   