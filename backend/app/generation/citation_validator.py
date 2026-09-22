
import re
from pydantic import BaseModel, Field


pattern = re.compile(r"[\[【]([^\]】]+)[\]】]")


class CitationResponse(BaseModel):
    chunk_id : str = Field(alias="chunkId")
    label:str
    valid:bool

def get_citation(text: str,hits : list[dict],dedupe: bool = True)->list[CitationResponse]:

    group = pattern.findall(text)

    group_set = set(group) if dedupe else group
    

    output = []

    lookup = {h["metadata"]["section_id"]: h["chunk_id"] for h in hits}

    for g in group_set:
        if g in lookup:
            output.append(CitationResponse(chunkId=lookup[g], label=g, valid=True))
        else:
            output.append(CitationResponse(chunkId="", label=g, valid=False))

    output.sort(key=lambda c : c.label)
    
    return output


def citation_validity(citations:list[CitationResponse]) -> float | None:
    if not citations:
        return None
    return sum(c.valid for c in citations) / len(citations)



def citation_correctness(citations: list[CitationResponse], expected_section_ids: list[str])-> float | None:
    if not citations:
        return None

    return sum(c.label in expected_section_ids for c in citations) / len(citations)


if __name__ == "__main__":
    def make(label, valid=True):
        return CitationResponse(chunkId="c-" + label, label=label, valid=valid)

    # --- citation_validity ---
    print(citation_validity([]))                                  # None  (empty)
    print(citation_validity([make("SEC-1")]))                     # 1.0   (all valid)
    print(citation_validity([make("SEC-1", False)]))              # 0.0   (all invalid)
    print(citation_validity([make("SEC-1"), make("SEC-2", False)]))  # 0.5 (half)

    # --- citation_correctness ---
    expected = ["SEC-1", "SEC-2"]

    print(citation_correctness([], expected))                                  # None (empty)
    print(citation_correctness([make("SEC-1"), make("SEC-2")], expected))      # 1.0  (all match)
    print(citation_correctness([make("SEC-9")], expected))                     # 0.0  (none match)
    print(citation_correctness([make("SEC-1"), make("SEC-9")], expected))      # 0.5  (half match)

    # Note: correctness counts by label, ignoring `valid` flag
    print(citation_correctness([make("SEC-1", False)], expected))              # 1.0