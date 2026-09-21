

from app.infra.groq_client import get_async_groq_client
from groq import RateLimitError
import time, random
import asyncio

SYSTEM_CHUNK_ANSWER = (
    "You answer questions about a legal contract using ONLY the numbered context "
    "clauses provided. If the answer is not in the context, say "
    "\"The provided clauses don't state this.\" Do not use outside knowledge. "
    "Quote the exact figure or deadline when the question asks for one.\n\n"
    "CITATION RULES:\n"
    "- Each context clause is labelled with a section number in square brackets before its text, e.g. [4.2].\n"
    "- When you cite a clause, copy its label EXACTLY as it appears in the brackets before that clause's text — "
    "character for character. Never shorten it, never lengthen it, never add letters or numbers that "
    "are not part of the label itself, even if the clause's text mentions sub-parts like (a) or (b).\n"
    "- Example: if the context shows '[1.2.2] The customer may (a) request a refund or (b) file a dispute...', "
    "the correct citation is [1.2.2] — NOT [1.2.2(a)] or [1.2.2(b)], because the label itself is only '1.2.2'.\n"
    "- Only cite labels that appear verbatim in the context. Never invent or guess a label.\n"
    "- Use exactly the [] bracket symbol. Correct: '...within thirty (30) days [10.3].' "
    "CRITICAL: Use ONLY plain ASCII square brackets: [ and ]. "
    "NEVER use 【 or 】 (full-width brackets) under any circumstances. "
    "If you are about to write 【, stop and write [ instead."
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


SYSTEM_REFINE = (
    "you'll be given a CURRENT SUMMARY (which may be empty on the first group) and a NEW EXCERPT of clauses, "
    "and must produce an UPDATED summary that incorporates the new excerpt while preserving everything already captured — don't drop or contradict prior content unless the new excerpt corrects it."
    "Each clause is labelled with its section number, e.g. [4.2(b)]. Cite the label of "
    "the clause each statement comes from. Only cite labels present in the context. "
    "Use exactly the [] bracket symbol for citations, never full-width brackets. "
    "Correct: '...within thirty (30) days [10.3].' "
    "Wrong — never do this: '...within thirty (30) days 【10.3】.'"
)

async def answer(question: str, context_chunks:list[str], override_user_message : str = None,system_prompt: str = SYSTEM_CHUNK_ANSWER, model : str = "openai/gpt-oss-20b")->str:
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
    user_message = f"Context clauses:\n{context_block}\n\n {override_user_message}" if override_user_message else f"Context clauses:\n{context_block}\n\nQuestion: {question}"
    
    response = await call_llm(user_message)
    return response.choices[0].message.content


async def summarize_context_map_reducer(query : str,context_chunks: list[dict]) -> str:
    return await answer(f"Give me a summary of the following contract clauses based on {query}", context_chunks=context_chunks, system_prompt=SYSTEM_SUMMARIZATION)

async def summarize_context_refine(question: str, current_summary: str, context_chunks: list[dict]) -> str:
    return await answer(
        question,
        context_chunks=context_chunks,
        override_user_message=(
            f"Original question: {question}\n"
            f"Current summary so far: {current_summary or '(none yet)'}\n\n"
            "Produce an updated summary that also works toward answering the original question."
        ),
        system_prompt=SYSTEM_REFINE,
    )


   
async def answer_with_stream(question: str, context_chunks: list, strategy: str, max_retries: int = 5, base_delay: float = 1.0):
    client = get_async_groq_client()
    if strategy == 'map_reduce' or strategy == 'refine':
        context_block = "\n\n".join(chunk for chunk in context_chunks)
    else:
        context_block = "\n\n".join(
            f'[{chunk["metadata"]["section_id"]}] {chunk["text"]}' for chunk in context_chunks
        )
    user_message = f"Context clauses:\n{context_block}\n\nQuestion: {question}"
    async def start_stream():
        for attempt in range(max_retries):
            try:
                return await client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": SYSTEM_CHUNK_ANSWER},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0,
                    stream=True,
                )
            except RateLimitError as e:
                if attempt == max_retries - 1:
                    raise
                print("Reach max_retries and need to sleep first")
                retry_after = e.response.headers.get("retry-after")
                delay = float(retry_after) if retry_after else base_delay * (2 ** attempt)
                await asyncio.sleep(delay + random.uniform(0, 0.5))
    response = await start_stream()
    async for chunk in response:
        piece = chunk.choices[0].delta.content
        if piece:
            yield piece