from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.retrieval.vector_store import doc_chunk_counts, get_collection
from datetime import datetime
from app.config import DOCUMENTS_DIR

from fastapi import HTTPException
import re



# Like `const router = express.Router()` + every path in here is prefixed with /query
router = APIRouter(prefix="/documents", tags=["documents"])

class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

class DocumentSummary(CamelModel):
    id: str
    title: str
    type: str
    status: str
    source: str
    chunk_count: int
    ingested_at: str

class Clause(BaseModel):
    id: str 
    heading: str
    text: str

class Section(BaseModel):
    id: str
    heading: str
    clauses: list[Clause]


class DocumentSection(DocumentSummary):
    sections: list[Section]

@router.get("/", response_model=list[DocumentSummary])
async def get_document_list():


    counts = doc_chunk_counts()
    summarys = []
    for s, c in counts.items():
        content = s.split("-", 1)
        type = content[0]
        title = content[1].title()
        status = "ready"
        source = s

        mtime = (DOCUMENTS_DIR / f"{s}.html").stat().st_mtime
        ingested_at = datetime.fromtimestamp(mtime).isoformat().split("T", 1)[0]


        summarys.append(DocumentSummary(id=s, title=title, type=type, status=status, source=source, chunk_count=c ,ingested_at=ingested_at))

    return summarys

@router.get("/{doc_id}", response_model=DocumentSection)
async def get_document(doc_id: str):

    counts = doc_chunk_counts()
    if doc_id not in counts:
        raise HTTPException(status_code=404, detail=f"no document {doc_id!r}")

    res = get_collection().get(where={"doc_id" : doc_id})
    texts, metas = res["documents"], res["metadatas"]
    # print(res)


    groups : dict[str, list[Clause]] = {}


    # gather the section id, 
    # getting the first num as the section after split
    # use it as a map to store the related clause
    for text, meta in zip(texts, metas):
        sid = meta["section_id"]
        num = sid.split(".")[0]
        groups.setdefault(num, []).append(Clause(id=sid, heading="", text=text))


    # clause multiple replace just in case contain like 4.2(a) like this
    # return only the digit like [4,2] so the sorted can sort the clauses
    sections = [
        Section(id=num, heading=f"Section {num}", clauses=sorted(cl, key = lambda c : [int(p) for p in c.id.replace("(",".").replace(")","").split(".") if p.isdigit()]))
        for num, cl in sorted(groups.items(), key=lambda kv: int(kv[0]))
    ]

  
    prefix, rest = doc_id.split("-", 1)
    
    mtime = (DOCUMENTS_DIR / f"{doc_id}.html").stat().st_mtime
    return DocumentSection(
        id=doc_id, title=rest.replace("-", " ").title(), type=prefix,
        status="ready", source=doc_id, chunk_count=counts[doc_id],
        ingested_at=datetime.fromtimestamp(mtime).isoformat().split("T")[0],
        sections=sections,
    )


  