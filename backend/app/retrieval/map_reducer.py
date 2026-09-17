from app.lib import estimate_tokens, sort_by_section

def map_reducer(chunks: list[dict], token_budget: int = 4000) -> list[dict]:
    ordered = sort_by_section(chunks)
    out = []
    kept = []
    used = 0
    total_token_budget =0
    for c in ordered:
        cost = estimate_tokens(c["text"])
        if used + cost > token_budget and kept:
            out.append(kept)      
            kept = []
            total_token_budget += (used + cost)             
            used = 0
            
        kept.append(c)
        used += cost
    total_token_budget+=used
    if kept:                      
        out.append(kept)
    print("token budget",total_token_budget)
    return out