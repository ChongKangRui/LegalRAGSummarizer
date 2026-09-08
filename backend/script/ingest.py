
from app.ingestion.loader import loadDocument
from app.ingestion.chunker import structural_chunk
from app.embedding.embedder import embed_documents
from app.retrieval.vector_store import reset, insert, count


def ingestProcess():
    reset()
    doc = loadDocument()
    print("-------------ingesting--------------")
    for d in doc:
        chunks = structural_chunk(d["text"], d["doc_id"])
        #print(chunks)
        vecs = embed_documents([c["text"] for c in chunks])
        print(f"inserting: {d["doc_id"]}")
        insert(chunks, vecs)
        
    print("-------------counting--------------")
    print(count())

if __name__ == "__main__":
    ingestProcess()
    