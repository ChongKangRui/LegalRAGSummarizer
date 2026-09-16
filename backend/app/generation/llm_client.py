

from app.infra.groq_client import get_groq_client
from groq import RateLimitError
import time, random

SYSTEM = (
      "You answer questions about a legal contract using ONLY the numbered context "
      "clauses provided. If the answer is not in the context, say "
      "\"The provided clauses don't state this.\" Do not use outside knowledge. "
      "Quote the exact figure or deadline when the question asks for one."
      "Each clause is labelled with its section number, e.g. [4.2(b)]. Cite the label of the clause each statement comes from. Only cite labels present in the context."
      "Ensure the cite label was using exactly the [] symbol not "
      "Here is an example of citation presentation: Correct: '...within thirty (30) days [10.3].'. Wrong — never do this: '...within thirty (30) days 【10.3】.'"
  )

def answer(question: str, context_chunks:list[str], model : str = "openai/gpt-oss-20b")->str:
    def with_retry(max_retries: int = 5, base_delay: float = 1.0):
        def decorator(fn):
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return fn(*args, **kwargs)
                    except RateLimitError as e:
                        if attempt == max_retries - 1:
                            raise
                        print("Reach max_retries and need to sleep first")
                        retry_after = e.response.headers.get("retry-after")
                        delay = float(retry_after) if retry_after else base_delay * (2 ** attempt)
                        time.sleep(delay + random.uniform(0, 0.5))
            return wrapper
        return decorator
    @with_retry()
    def call_llm(user_message: str):
        client = get_groq_client()
        return client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
        )

    context_block = "\n\n".join(
        f'[{chunk["metadata"]["section_id"]}] {chunk["text"]}' for chunk in context_chunks
    )
    user_message = f"Context clauses:\n{context_block}\n\nQuestion: {question}"
    
    response = call_llm(user_message)
    return response.choices[0].message.content

def answer_with_stream(question: str, context_chunks:list[str]):
    client = get_groq_client()
    context_block = "\n\n".join(
        f"[{chunk["metadata"]["section_id"]}] {chunk["text"]}" for chunk in context_chunks
        )
    user_message = f"Context clauses:\n{context_block}\n\nQuestion: {question}"
    response = client.chat.completions.create(
     model="openai/gpt-oss-20b",
     messages=[
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_message},
    ],
    temperature=0,
    stream=True
    )

    for chunk in response:
        piece = chunk.choices[0].delta.content
      
        if piece:
            yield piece
   