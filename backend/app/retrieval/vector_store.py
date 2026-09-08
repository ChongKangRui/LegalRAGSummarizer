from collections import defaultdict
from app.config import DATA_DIR

import chromadb 
from functools import cache


@cache
def get_chroma_client() -> chromadb.ClientAPI:
    client = chromadb.PersistentClient(path=str(DATA_DIR/"chroma"))
    return client

def get_collection()->chromadb.Collection:
    return get_chroma_client().get_or_create_collection(name="my_collection", metadata={"hnsw:space": "cosine"})


def insert(chunk: list[dict],vectors:list[list[float]]):

    if len(chunk) != len(vectors):
        raise ValueError("Chunk length not equal to vectors length. Both should be equal so upsert can work")

    
    ids = [c["chunk_id"] for c in chunk]
    embeddings = vectors
    metadatas = [c["metadata"] for c in chunk]
    documents = [c["text"] for c in chunk]
   
    get_collection().upsert(ids=ids,
    embeddings=embeddings,
    metadatas=metadatas,
    documents=documents)
   

def count()->int:
    return get_collection().count()

def reset():
    try:
        get_chroma_client().delete_collection(name="my_collection")
    except chromadb.errors.NotFoundError:
        pass

def query(query_vector: list[float], top_k: int = 10, where: dict | None = None)->chromadb.QueryResult:
    return get_collection().query(query_embeddings=query_vector, n_results=top_k, where=where)


def doc_chunk_counts()->dict[str, int]:
    """{doc_id: number of chunks} for everything currently in the store."""
    metadatas = get_collection().get(include=["metadatas"])["metadatas"]

    counts = defaultdict(int)
    for m in metadatas:
        counts[m["doc_id"]] += 1

    return counts

if __name__ == "__main__":
    
    from app.ingestion.loader import loadDocument
    from app.ingestion.chunker import structural_chunk
    from app.embedding.embedder import embed_documents
    doc = loadDocument()[0]
    chunks = structural_chunk(doc["text"], doc["doc_id"])
    #print(chunks)
    vecs = embed_documents([c["text"] for c in chunks])

    insert(chunks, vecs)