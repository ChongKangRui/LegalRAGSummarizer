

from app.infra.groq_client import get_async_groq_client
from groq import RateLimitError
import time, random
import asyncio

SYSTEM_CHUNK_ANSWER = (
      "You answer questions about a legal contract using ONLY the numbered context "
      "clauses provided. If the answer is not in the context, say "
      "\"The provided clauses don't state this.\" Do not use outside knowledge. "
      "Quote the exact figure or deadline when the question asks for one."
      "Each clause is labelled with its section number, e.g. [4.2(b)]. Cite the label of the clause each statement comes from. Only cite labels present in the context."
      "Ensure the cite label was using exactly the [] symbol not "
      "Here is an example of citation presentation: Correct: '...within thirty (30) days [10.3].'. Wrong — never do this: '...within thirty (30) days 【10.3】.'"
  )



SYSTEM_SUMMARIZATION = (
    "You are summarizing one excerpt of a larger legal contract. This excerpt may not "
    "cover the whole agreement, so do not claim it does or state what the contract "
    "'only' covers based on this excerpt alone. "
    "Use ONLY the numbered context clauses provided — do not rely on outside knowledge. "
    "Write a concise summary covering the key obligations, rights, deadlines, and "
    "restrictions in this excerpt. Always quote the exact figure or deadline whenever "
    "one is stated. "
    "Each clause is labelled with its section number, e.g. [4.2(b)]. Cite the label of "
    "the clause each statement comes from. Only cite labels present in the context. "
    "Use exactly the [] bracket symbol for citations, never full-width brackets. "
    "Correct: '...within thirty (30) days [10.3].' "
    "Wrong — never do this: '...within thirty (30) days 【10.3】.'"
)

async def answer(question: str, context_chunks:list[str], system_prompt: str = SYSTEM_CHUNK_ANSWER, model : str = "openai/gpt-oss-20b")->str:
    def with_retry(max_retries: int = 5, base_delay: float = 1.0):
        def decorator(fn):
            async def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return await fn(*args, **kwargs)
                    except RateLimitError as e:
                        if attempt == max_retries - 1:
                            raise
                        print("Reach max_retries and need to sleep first")
                        retry_after = e.response.headers.get("retry-after")
                        delay = float(retry_after) if retry_after else base_delay * (2 ** attempt)
                        await asyncio.sleep(delay + random.uniform(0, 0.5))
            return wrapper
        return decorator
    @with_retry()
    async def call_llm(user_message: str):
        client = get_async_groq_client()
        return await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
        )

    context_block = "\n\n".join(
        f'[{chunk["metadata"]["section_id"]}] {chunk["text"]}' for chunk in context_chunks
    )
    user_message = f"Context clauses:\n{context_block}\n\nQuestion: {question}"
    
    response = await call_llm(user_message)
    return response.choices[0].message.content


async def summarize_context(query : str,context_chunks: list[dict]) -> str:
    return await answer(f"Give me a summary of the following contract clauses based on {query}", context_chunks=context_chunks, system_prompt=SYSTEM_SUMMARIZATION)




async def answer_with_stream(question: str, context_chunks:list, strategy: str):
    client = get_async_groq_client()
    
    context_block = ""

    
    if strategy == 'map_reduce':
        context_block = "\n\n".join(
            chunk for chunk in context_chunks
            )
    else:
        context_block = "\n\n".join(
            f"[{chunk["metadata"]["section_id"]}] {chunk["text"]}" for chunk in context_chunks
            )
         
        
    user_message = f"Context clauses:\n{context_block}\n\nQuestion: {question}"
    response = await client.chat.completions.create(
     model="openai/gpt-oss-20b",
     messages=[
        {"role": "system", "content": SYSTEM_CHUNK_ANSWER},
        {"role": "user", "content": user_message},
    ],
    temperature=0,
    stream=True
    )

    async for chunk in response:
        piece = chunk.choices[0].delta.content
      
        if piece:
            yield piece
   