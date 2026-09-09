"""Vector-store façade.

Picks a backend from config.VECTOR_BACKEND (env: VECTOR_BACKEND=chroma|numpy) and
re-exports its functions, so callers never import a backend directly.

Every backend implements the same contract:
  insert(chunks, vectors)                    -> None
  query(query_vector, top_k=10, where=None)  -> list[dict]  (chunk + "score", higher = better)
  get_chunks(doc_id)                         -> list[dict]
  count()                                    -> int
  doc_chunk_counts()                         -> dict[str, int]
  reset()                                    -> None

where a chunk is {"chunk_id": str, "text": str, "metadata": {"doc_id":…, "section_id":…}}.
"""

from app.config import VECTOR_BACKEND

if VECTOR_BACKEND == "chroma":
    from app.retrieval import chroma_store as _backend
elif VECTOR_BACKEND == "numpy":
    from app.retrieval import numpy_store as _backend
else:
    raise ValueError(
        f"unknown VECTOR_BACKEND {VECTOR_BACKEND!r} — expected 'chroma' or 'numpy'"
    )

insert = _backend.insert
query = _backend.query
get_chunks = _backend.get_chunks
count = _backend.count
doc_chunk_counts = _backend.doc_chunk_counts
reset = _backend.reset

__all__ = ["insert", "query", "get_chunks", "count", "doc_chunk_counts", "reset"]
