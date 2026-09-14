"""One-off helper: list available clause ids per document, for golden-set labeling.
Not part of the app — reads whatever ingest.py already produced."""
import json
from collections import defaultdict
from app.config import VECTORS_META

def build_reference():
    with open(VECTORS_META, encoding="utf-8") as f:
        chunks = json.load(f)

    by_doc = defaultdict(list)
    for chunk in chunks:
        meta = chunk["metadata"]
        by_doc[meta["doc_id"]].append({
            "section_id": meta["section_id"],
            "preview": chunk["text"][:120].replace("\n", " "),
        })
    return by_doc


if __name__ == "__main__":
    for doc_id, clauses in build_reference().items():
        print(f"\n=== {doc_id} ({len(clauses)} clauses) ===")
        for c in clauses:
            print(f"  {c['section_id']:>10}  {c['preview']}")