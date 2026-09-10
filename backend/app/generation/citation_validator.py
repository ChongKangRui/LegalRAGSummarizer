
import re
from pydantic import BaseModel, ConfigDict, Field


pattern = re.compile(r"\[([^\]]+)\]")


class CitationResponse(BaseModel):
    chunk_id : str = Field(alias="chunkId")
    label:str
    valid:bool

def get_citation(text: str, hits : list[dict])->list[CitationResponse]:

    group = pattern.findall(text)
    group_set = set(group)
    output = []

    lookup = {h["metadata"]["section_id"]: h["chunk_id"] for h in hits}

    for g in group_set:
        if g in lookup:
            output.append(CitationResponse(chunkId=lookup[g], label=g, valid=True))
        else:
            output.append(CitationResponse(chunkId="", label=g, valid=False))

    output.sort(key=lambda c : c.label)
    
    return output
