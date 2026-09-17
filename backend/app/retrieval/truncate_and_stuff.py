from app.lib import estimate_tokens, sort_by_section



def truncate_and_stuff(chunks: list[dict], token_budget: int = 4000) -> list[dict]:
    ordered = sort_by_section(chunks)
    kept = []
    used = 0
    for c in ordered:
        cost = estimate_tokens(c["text"])
        if used + cost > token_budget:
            break
        kept.append(c)
        used += cost
    return kept