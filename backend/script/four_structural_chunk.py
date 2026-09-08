import re

from script.one_naive_baseline import DOCUMENT
from script.three_generate_answer import answer
from script.two_embed_similarity import retrieve

CLAUSE_RE =re.compile(r"^(\d+\.\d+(?:\([a-z]\))?)\s", re.MULTILINE)

matches = list(CLAUSE_RE.finditer(DOCUMENT))

clauses = []

for i,m in enumerate(matches):
    start = m.start()
    end = matches[i+1].start() if i + 1 < len(matches) else len(DOCUMENT)

    clauses.append({"section_id": m.group(1), "text": DOCUMENT[start:end].strip()})

for c in clauses:
    print(f"--- [{c['section_id']}] ({len(c['text'])} chars) ---")
    print(c["text"])
    print()

question = "How much time does licensee have to pay an invoice?"
clause_texts = [c["text"] for c in clauses]

print(f"\n=== retrieval over structural chunks ===\nQ: {question}\n")
# for rank, text in enumerate(retrieve(question, clause_texts, top_k=3), start=1):
#     print(f"#{rank}  {text}\n")
#     print()

for k in (1, 3):
    ctx = retrieve(question, clause_texts, top_k=k)
    print(f"\n=== structural chunks, top_k={k} ===")
    print(answer(question, ctx))