
import re
import app.ingestion.loader as loader
CLAUSE_RE =re.compile(r"^(\d+\.\d+(?:\([a-z]\))?)\.?(?:\s|$)", re.MULTILINE)


def naive_chunk(text: str, doc_id: str, chunk_size: int = 200) -> list[dict]:
    """Split into fixed-size windows, ignoring sentence/clause boundaries — on purpose."""

    outputDict = []

    for i in range(0, len(text), chunk_size):
        t = text[i : i + chunk_size]
        outputDict.append({"chunk_id" : f"{doc_id}::chunk-{i}", "text" : t, "metadata" : {"doc_id":doc_id, "chunk_index" : i}})


    return outputDict

def structural_chunk(text: str, doc_id: str)->list[dict]:
    matches = list(CLAUSE_RE.finditer(text))
    output = []
    for i,m in enumerate(matches):
        start = m.start()
        end = matches[i+1].start() if i + 1 < len(matches) else len(text)

        final_text = text[m.end():end].strip()
    

        output.append({"chunk_id":f"{doc_id}::chunk-{m.group(1)}::{i}", "text": final_text, "metadata" : {"doc_id":doc_id, "section_id" : f"{m.group(1)}"}})

    return output
#matches = list(CLAUSE_RE.finditer(DOCUMENT))

if __name__ == "__main__":
    output = loader.loadDocument()
    for d in output:
        print(f"Loaded Document {d["doc_id"]}")
        #chunks = naive_chunk(d["text"], d["doc_id"])
        chunks = structural_chunk(d["text"], d["doc_id"]);
        print("======================================")
        for c in chunks:
            print(f"chunk id {c["chunk_id"]}")
        print("===============NEXTNEXTNEXT================")
       
        
    