def estimate_tokens(text: str) -> int:
    return int(len(text.split()) * 1.3)

def sort_by_section(chunks: list[dict]) -> list[dict]:
    def key(c):
        parts = c["metadata"]["section_id"].replace("(", ".").replace(")", "").split(".")
        return [int(p) for p in parts if p.isdigit()]
    return sorted(chunks, key=key)