
from app.ingestion.loader import loadDocument
from app.ingestion.chunker import structural_chunk
from app.embedding.embedder import embed_documents
from app.retrieval.vector_store import reset, insert, count
import numpy as np

import time

def dedupe(all_chunks : list, vecs : list[list[float]], threshold : float = 0.99):
    V = np.asarray(vecs, dtype=np.float32)
    keep = []
    for i in range(len(all_chunks)):
        if keep and (V[keep] @ V[i]).max() >= threshold:
            continue
        keep.append(i)

    chunks = [all_chunks[i] for i in keep]
    vecs   = [vecs[i] for i in keep]

    return chunks, vecs


def ingestProcess():
    reset()
    docs = loadDocument()
    print("-------------ingesting--------------")
    all_chunks, all_vecs = [], []

    for d in docs:
        t0 = time.perf_counter()
        chunks = structural_chunk(d["text"], d["doc_id"])
        vecs = embed_documents([c["text"] for c in chunks])
        all_chunks.extend(chunks)
        all_vecs.extend(vecs)
        print(f"  {d['doc_id']:<32} {len(chunks):>4} chunks  {time.perf_counter()-t0:6.1f}s")

    # vecs = embed_documents([c["text"] for c in all_chunks])   # embed everything first
    chunks, vecs = dedupe(all_chunks, all_vecs, threshold=0.99)   # then filter both together
    insert(chunks, vecs)
        
    print("-------------counting--------------")
    print(count())

if __name__ == "__main__":
    ingestProcess()
    