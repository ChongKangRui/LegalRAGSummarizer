"""Brute-force numpy implementation of the vector-store interface.

Same contract as `chroma_store` — see that module for the shapes:
  chunk  -> {"chunk_id": str, "text": str, "metadata": {"doc_id":…, "section_id":…}}
  hit    -> chunk + {"score": float}   (higher = more similar)

Persistence is two files written by `ingest.py`:
  config.VECTORS_PATH  -> np.ndarray, shape (n_chunks, 384), float32, L2-normalized
  config.VECTORS_META  -> JSON list of the chunk dicts, row i describes vector i

Because fastembed L2-normalizes, cosine similarity is just the dot product:
`V @ q` gives one score per chunk, then argsort for top-k. No index, exact results.

"""

import json
from functools import cache
import numpy as np
from app.config import VECTORS_PATH, VECTORS_META, EMBED_DIM


@cache
def _load() -> tuple["np.ndarray", list[dict]]:
    """Load the store from disk. Cached for the process lifetime.
    
        Returns two halves of the same data, linked ONLY by position:
    
          V     ndarray (n_chunks, 384) float32 — the MATH.
                V[i] is chunk i's embedding. Contains no text, no ids.
                L2-normalized by fastembed, so V @ q is cosine similarity.
                Basically the vector of embedding
    
          meta  list[dict], length n_chunks — the MEANING.
                meta[i] = {"chunk_id":…, "text":…, "metadata": {"doc_id":…, "section_id":…}}
    
        V[i] and meta[i] are the same chunk. Nothing enforces this but insert()'s
        length check — never reorder or filter one without the other.
    """
    if not VECTORS_PATH.exists() or not VECTORS_META.exists():
        return np.zeros((0, EMBED_DIM), dtype=np.float32),[]

    array = np.load(VECTORS_PATH)
    with open(VECTORS_META, encoding="utf-8") as f:
        meta = json.load(f)

    return array, meta


def insert(chunks: list[dict], vectors: list[list[float]]) -> None:
    """Write vectors to VECTORS_PATH and chunks to VECTORS_META.

    Unlike Chroma there's no upsert — this rewrites both files wholesale, so
    `ingest.py` must accumulate every document's chunks before calling it once.
    """

    if len(chunks) != len(vectors):
            raise ValueError(
                f"chunks ({len(chunks)}) and vectors ({len(vectors)}) must be the same length"
            )

    v = np.asarray(vectors, dtype=np.float32)
    VECTORS_PATH.parent.mkdir(parents=True, exist_ok=True)

    np.save(VECTORS_PATH, v)
    with open(VECTORS_META, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)
    _load.cache_clear()



def query(
    query_vector: list[float], top_k: int = 10, where: dict | None = None
) -> list[dict]:
    """scores = V @ q  ->  mask out rows failing `where`  ->  argsort  ->  top_k."""
    vectors, meta = _load()

    if not meta:
        return []

    q = np.asarray(query_vector, dtype=np.float32)
    scores = vectors @ q

    if where:
        mask = np.fromiter((all(m["metadata"].get(k) == v for k,v in 
        where.items()) for m in meta), 
        dtype=bool,
        count=len(meta))
        
        scores = np.where(mask, scores, -np.inf)

    idx = np.argsort(scores)[::-1][:top_k]

    return [
        {**meta[i], "score": float(scores[i])}
        for i in idx
        if np.isfinite(scores[i])
    ]


def get_chunks(doc_id: str) -> list[dict]:
    """Filter the metadata list on metadata["doc_id"]."""
    _, meta = _load()
    return [m for m in meta if m["metadata"]["doc_id"] == doc_id]


def count() -> int:
    _, meta = _load()
    return len(meta)



def doc_chunk_counts() -> dict[str, int]:
    _, meta = _load()
    from collections import Counter
    doc_counter = Counter(m["metadata"]["doc_id"] for m in meta)
   
    return dict(doc_counter)



def reset() -> None:
    VECTORS_PATH.unlink(missing_ok=True)
    VECTORS_META.unlink(missing_ok=True)
    _load.cache_clear()

