

"""Naive RAG, end to end: retrieve fixed-size chunks -> stuff into a prompt -> Groq answers.

Builds on the Phase 1 baseline. Watch what happens to clause 4.1, which the naive
chunker splits across two chunks (see two_embed_similarity.py).
"""

from one_naive_baseline import DOCUMENT
from two_embed_similarity import naive_chunk, retrieve

#question = "How much time does licensee have to pay an invoice?"
# question = "What is the annual license fee amount?"
# context_chunks = retrieve(question, naive_chunk(DOCUMENT), top_k=3)

# for i, chunk in enumerate(context_chunks):
#     print(f"[chunk {i}]\n{chunk}\n")

SYSTEM = (
      "You answer questions about a legal contract using ONLY the numbered context "
      "clauses provided. If the answer is not in the context, say "
      "\"The provided clauses don't state this.\" Do not use outside knowledge. "
      "Quote the exact figure or deadline when the question asks for one."
  )

# context_block = "\n\n".join(
#     f"[{i}] {chunk}" for i, chunk in enumerate(context_chunks)
# )

# user_message = f"Context clauses:\n{context_block}\n\nQuestion: {question}"
# print("=== SYSTEM ===")
# print(SYSTEM)
# print("\n=== USER ===")
# print(user_message)


# Now calling ai to answer this

import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])


def answer(question:str, context_chunks: list[str])->str:
    context_block = "\n\n".join(
    f"[{i}] {chunk}" for i, chunk in enumerate(context_chunks)
    )
    user_message = f"Context clauses:\n{context_block}\n\nQuestion: {question}"
    response = client.chat.completions.create(
     model="openai/gpt-oss-20b",
     messages=[
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_message},
    ],
    )

    return response.choices[0].message.content

if __name__ == "__main__":
    question = "How much time does licensee have to pay an invoice?"
    ctx = retrieve(question, naive_chunk(DOCUMENT), top_k=3)
    print(answer(question, ctx))