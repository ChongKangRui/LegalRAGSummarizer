"""Chroma implementation of the vector-store interface.

Returns backend-neutral shapes so `numpy_store` can be swapped in:
  chunk  -> {"chunk_id": str, "text": str, "metadata": {"doc_id":…, "section_id":…}}
  hit    -> chunk + {"score": float}   (higher = more similar)
"""

from collections import defaultdict
from functools import cache

import chromadb

from app.config import DATA_DIR

COLLECTION = "my_collection"


@cache
def _client() -> chromadb.ClientAPI:
    return chromadb.PersistentClient(path=str(DATA_DIR / "chroma"))


def _collection() -> chromadb.Collection:
    return _client().get_or_create_collection(
        name=COLLECTION, metadata={"hnsw:space": "cosine"}
    )


def insert(chunks: list[dict], vectors: list[list[float]]) -> None:
    if len(chunks) != len(vectors):
        raise ValueError(
            f"chunks ({len(chunks)}) and vectors ({len(vectors)}) must be the same length"
        )

    _collection().upsert(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=vectors,
        metadatas=[c["metadata"] for c in chunks],
        documents=[c["text"] for c in chunks],
    )


def query(
    query_vector: list[float], top_k: int = 10, where: dict | None = None
) -> list[dict]:
    """Top-k most similar chunks. `where` filters on metadata, e.g. {"doc_id": "..."}."""
    r = _collection().query(
        query_embeddings=[query_vector], n_results=top_k, where=where
    )
    # Chroma batches by query vector -> unwrap [0]. Cosine space returns a
    # distance (1 - similarity); flip it so higher = better, like numpy's dot product.
    return [
        {"chunk_id": cid, "text": text, "metadata": meta, "score": 1.0 - dist}
        for cid, text, meta, dist in zip(
            r["ids"][0], r["documents"][0], r["metadatas"][0], r["distances"][0]
        )
    ]


def get_chunks(doc_id: str) -> list[dict]:
    """Every chunk belonging to one document, unordered."""
    r = _collection().get(where={"doc_id": doc_id})
    return [
        {"chunk_id": cid, "text": text, "metadata": meta}
        for cid, text, meta in zip(r["ids"], r["documents"], r["metadatas"])
    ]


def count() -> int:
    return _collection().count()


def doc_chunk_counts() -> dict[str, int]:
    """{doc_id: number of chunks} for everything currently in the store."""
    counts: dict[str, int] = defaultdict(int)
    for m in _collection().get(include=["metadatas"])["metadatas"]:
        counts[m["doc_id"]] += 1
    return dict(counts)


def reset() -> None:
    try:
        _client().delete_collection(name=COLLECTION)
        
    except chromadb.errors.NotFoundError:
        pass
