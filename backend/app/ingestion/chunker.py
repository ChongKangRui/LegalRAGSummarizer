"""Split document text into retrievable chunks.

Two strategies:
  naive_chunk      fixed-size windows, structure-blind. Kept as the Phase 4 eval
                   control — the baseline that structural chunking has to beat.
  structural_chunk splits on clause labels (1.1, 1.1.4, 4.2(b)) so a chunk is a
                   real clause rather than an arbitrary window.

Chunk size is bounded on both ends, for opposite reasons:
  too small -> the text loses the meaning that lived in its parent clause
               ("posting URLs to external websites;" never says it's prohibited)
  too large -> bge-small truncates at 512 tokens, so everything past the limit is
               stored but unsearchable
"""

import re

import app.ingestion.loader as loader

# Clause labels: 1.1 / 1.1.4 / 4.2(b), with an optional trailing dot.
CLAUSE_RE = re.compile(r"^(\d+\.\d+(?:\.\d+)?(?:\([a-z]\))?)\.?(?:\s|$)", re.MULTILINE)
# Bare section headings: "5. Software Products". The capital is a lookahead so the
# match ends before it — otherwise the slice would eat the title's first letter.
HEADING_RE = re.compile(r"^(\d{1,2})\.\s+(?=[A-Z])", re.MULTILINE)

# Below this, a chunk is a bare heading or a table-of-contents entry — a title with
# no body. It can never answer a question, so it is dropped rather than indexed.
MIN_CHUNK_SIZE = 40
# Below this, a clause is usually a fragment that needs its parent's context.
SMALL_CLAUSE_SIZE = 150
# Measured: 512 tokens is 1471-2518 chars on this corpus. 1400 stays under the
# worst case, so no chunk is silently truncated at embedding time.
OVERSIZE_CLAUSE_SIZE = 1400


def pack(parts, sep, limit):
    """Greedily join parts, starting a new piece only when the next would overflow.

    Keeps pieces near the limit instead of cutting at every separator, so as much
    context as possible stays together.
    """
    out, buf = [], ""
    for p in parts:
        # Don't flush a buffer that is still just a heading — a slight overflow
        # beats orphaning a title from the text it introduces.
        if buf and len(buf) >= MIN_CHUNK_SIZE and len(buf) + len(p) + len(sep) > limit:
            out.append(buf)
            buf = p
        else:
            buf = f"{buf}{sep}{p}" if buf else p
    if buf:
        out.append(buf)
    return out


def split_oversized(text):
    """Cut text down to embeddable pieces, preferring the least disruptive break.

    Lines first, sentences only where a single line is still too long. The loader
    strips blank lines, so "\\n" is the coarsest break available. Measured on this
    corpus: no single sentence exceeds the limit, so no character-level fallback.
    """
    if len(text) <= OVERSIZE_CLAUSE_SIZE:
        return [text]

    pieces = []
    for piece in pack(text.split("\n"), "\n", OVERSIZE_CLAUSE_SIZE):
        pieces.extend(
            pack(piece.split(". "), ". ", OVERSIZE_CLAUSE_SIZE)
            if len(piece) > OVERSIZE_CLAUSE_SIZE
            else [piece]
        )
    return pieces


def naive_chunk(text: str, doc_id: str, chunk_size: int = 200) -> list[dict]:
    """Split into fixed-size windows, ignoring sentence/clause boundaries — on purpose."""
    outputDict = []

    for i in range(0, len(text), chunk_size):
        t = text[i : i + chunk_size]
        outputDict.append({"chunk_id" : f"{doc_id}::chunk-{i}", "text" : t, "metadata" : {"doc_id":doc_id, "chunk_index" : i}})


    return outputDict

def structural_chunk(text: str, doc_id: str)->list[dict]:
    """Split text at clause boundaries, then bound the result on both ends.

    Two passes, in this order: merging can push a clause over the size limit, so
    the final size isn't known until all merging is done.
    """
    matches = list(CLAUSE_RE.finditer(text)) + list(HEADING_RE.finditer(text))
    matches.sort(key=lambda m: m.start())

    # Pass 1 — one chunk per clause, absorbing fragments into their parent.
    output = []
    for i,m in enumerate(matches):

        end = matches[i+1].start() if i + 1 < len(matches) else len(text)
        sid = m.group(1)

        parent = output[-1]["metadata"]["section_id"] if output else None
        final_text = text[m.end():end].strip()

        # Only a genuine child may merge (1.1.4 into 1.1). Absorbing a sibling
        # would leave a chunk labelled 1.1.5 that actually contains 1.1.6's text,
        # which makes its citation wrong. Orphan fragments stay standalone.
        if len(final_text) < SMALL_CLAUSE_SIZE and parent and sid.startswith(parent + "."):
            output[-1]["text"] += "\n" + final_text 
        else:
            output.append({"chunk_id":f"{doc_id}::chunk-{m.group(1)}::{i}", "text": final_text, "metadata" : {"doc_id":doc_id, "section_id" : f"{m.group(1)}"}})

    # Titles with no body (headings, index entries) carry no answerable content.
    output = [c for c in output if len(c["text"]) >= MIN_CHUNK_SIZE]

    # Pass 2 — break up anything still too large to embed.
    result = []

    for c in output:
        pieces = split_oversized(c["text"])
        if len(pieces) == 1:
            result.append(c)
        else:
            # Pieces share the parent's section_id so [§1.1] stays a valid
            # citation whichever piece the model read; only chunk_id must differ.
            for i, piece in enumerate(pieces, 1):
                result.append({"chunk_id":f"{c["chunk_id"]}::{i}", "text": piece,
                                "metadata" : {**c["metadata"], "part" : f"{i}"}})


    return result

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
