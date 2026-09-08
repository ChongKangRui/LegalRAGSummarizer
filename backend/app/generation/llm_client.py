

from app.infra.groq_client import get_groq_client

SYSTEM = (
      "You answer questions about a legal contract using ONLY the numbered context "
      "clauses provided. If the answer is not in the context, say "
      "\"The provided clauses don't state this.\" Do not use outside knowledge. "
      "Quote the exact figure or deadline when the question asks for one."
  )

def answer(question: str, context_chunks:list[str])->str:
    client = get_groq_client()
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

def answer_with_stream(question: str, context_chunks:list[str]):
    client = get_groq_client()
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
    stream=True
    )

    for chunk in response:
        piece = chunk.choices[0].message.content
        if piece
            yield chunk.choices[0].message.content
