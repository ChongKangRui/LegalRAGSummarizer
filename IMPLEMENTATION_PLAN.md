# Legal RAG Summarizer — Implementation & Target Plan

## Context

This is a RAG / AI-engineering project, built from scratch. The repo currently has a bare FastAPI backend (`main.py`, `uv`, Python 3.14) and frontend react folder. 

The goal isn't a polished product — it's to actually learn RAG, using legal text because it forces four lessons naive tutorials skip:
- **Structural chunking** — clauses and sections reference each other; fixed-size chunks break that.
- **Grounded citation** — every claim should trace back to a specific clause.
- **Retrieval quality** — learning to notice (and fix) when the wrong clause gets retrieved.
- **Long-context handling** — real documents are long enough to hit actual context limits.

Two decisions are already made, with reasoning in [TECH_STACK.md](./TECH_STACK.md):
- Build the RAG pipeline **by hand**, not with LangChain/LlamaIndex.
- **Local embeddings + Groq (free tier)** for generation.

## Target — Definition of Done

A working app where you can:
1. Load a legal document (statute, case opinion, ToS, or a real contract from SEC EDGAR).
2. See it chunked by actual structure (clauses/sections), not fixed-size windows.
3. Ask a question and get results from **hybrid search** (vector + BM25) plus a **reranker**, not vector search alone.
4. Get an answer where every point cites its source clause (`[§4.2(b)]`), with a validator that catches citations that don't map to a real chunk.
5. For long documents, get a real multi-pass summary (map-reduce/refine) — and compare it against a naive truncated one to see what gets lost.
6. Run an eval harness against a small labeled Q&A set, so retrieval changes show up as numbers (precision/recall@k), not guesses.

## Tech Stack

See **[TECH_STACK.md](./TECH_STACK.md)** for the stack, rationale, and data sources.

## Application Feature Scope (beyond the AI pipeline)

The RAG pipeline (ingest → chunk → retrieve → cite → summarize → eval) is the core of this project. But an app needs a bit more to be usable — and a few extra features can make the RAG work visible instead of hidden behind a text box. Avoid two traps: a bare Q&A box (too thin), or a full SaaS shell with accounts (scope that teaches infra, not RAG).

**MVP — needed to use the app at all**
- **Library** — browse a curated set of pre-ingested sample docs (statutes, case law, ToS, EDGAR contracts) with type, date, chunk count. No public upload — see [Going live](#going-live-public-no-accounts) below for why.
- **Document viewer** — see the source text alongside retrieved chunks.
- **Ask/Summarize** — ask a question or request a summary, see the answer with inline citations.

**Nice-to-have — cheap, and reinforces what you're learning**
- **Retrieval inspector** — retrieved chunks with vector/BM25/rerank scores side by side, highlighted in the document. The best feature for making hybrid search + reranking tangible.
- **Eval dashboard** — a page rendering the eval script's output (precision/recall/MRR per pipeline stage) instead of a CLI-only report.
- **Compare mode** — same query, two pipeline configs, results side by side (e.g. naive vs. structural chunking).
- **Summary export** — download a summary + citations as Markdown.

**Skip for now — real features, but they teach infra, not RAG**
- Multi-user accounts/auth — no per-user anything, so there's nothing to log into.
- Public document upload — see [Going live](#going-live-public-no-accounts): the library stays curated by you, not visitors.
- Persistent query/session history — nice later, not needed for a shared, accountless app.
- Redlining, risk-flagging, cross-contract comparison — good next-project ideas, not v1 scope.
- Batch ingestion with a job queue — you ingest docs yourself, one at a time, via the fetch/ingest scripts.

### Suggested frontend pages
1. **Library** — browse curated docs.
2. **Document view** — source + Ask/Summarize + citations.
3. **Inspector** — retrieval scores per chunk.
4. **Eval dashboard** — metrics from the golden-set eval.
5. **Compare** — two configs, side by side.

## Going live (public, no accounts)

No login and no per-user data — but "no database at all" isn't quite right. Chroma already is one (vector data); going public just needs a little more, still with zero accounts:

- **Document registry (SQLite)** — the Library page needs a clean list of documents (title, type, status). Reconstructing that from Chroma's per-chunk metadata works but is awkward; a small table is simpler.
- **Rate limiting (SQLite or in-memory, per IP)** — once it's public, everyone shares one Groq free-tier quota. Without a request cap, one visitor can exhaust it for everyone else. This becomes a requirement at launch, not a nice-to-have.
- **Curated library only, no public upload** — the app decided against letting visitors upload their own documents. That avoids storing strangers' files, per-visitor cleanup, and a much bigger upload-abuse surface — you control what's in the library by running the ingest scripts yourself.

See [TECH_STACK.md](./TECH_STACK.md) for where SQLite fits alongside Chroma.

## Learning-goal → phase map
- Structural chunking → Phase 2
- Grounded citation → Phase 3
- Retrieval quality eval → Phase 4
- Long-context handling → Phase 5

## Proposed backend layout

```
backend/
  app/
    ingestion/
      loaders.py            # PDF/HTML/text -> raw text per doc type
      structure_parser.py   # doc-type-aware parser -> Document/Section/Clause tree
      chunker.py             # naive fixed-size (Phase1) + structural chunker (Phase2)
    embeddings/
      embedder.py             # sentence-transformers wrapper
    retrieval/
      vector_store.py         # Chroma wrapper
      keyword_store.py        # BM25 wrapper
      hybrid.py                 # Reciprocal Rank Fusion
      reranker.py                # cross-encoder rerank
    generation/
      llm_client.py             # provider adapter (Groq now, Ollama/Gemini pluggable)
      prompts.py                 # citation-aware prompt templates
      citation_validator.py      # post-hoc check: every citation maps to a retrieved chunk
      summarizer.py               # naive-truncate / map-reduce / refine strategies
    eval/
      golden_set.json             # hand-labeled question -> expected clause id(s)
      retrieval_eval.py           # precision@k/recall@k/MRR
      run_eval.py                  # CLI: run a pipeline config against the golden set, print metrics
    api/
      routes.py                    # /query, /summarize, /eval (no public /ingest — library is curated)
      rate_limit.py                 # per-IP request cap middleware
    storage/
      registry.py                   # SQLite: document registry (id, title, type, status, chunk_count)
    models.py                      # pydantic: Chunk, Citation, SummaryResponse, EvalResult
  data/
    raw/          # downloaded source docs (gitignored)
    processed/     # parsed/chunked intermediate JSON (gitignored)
    chroma/         # Chroma persistence dir (gitignored)
    app.db           # SQLite: registry + rate-limit counters (gitignored)
  scripts/
    fetch_edgar_contracts.py
    fetch_courtlistener_cases.py
    fetch_statutes.py
    ingest.py           # you run this yourself to add a doc to the curated library
frontend/                # React + Vite + Tailwind
  src/
    pages/
      Library.tsx          # (Phase 1+)
      DocumentView.tsx      # (Phase 1+)
      Inspector.tsx          # (Phase 4+)
      EvalDashboard.tsx        # (Phase 4+)
      Compare.tsx                # (Phase 5+)
    components/
    lib/                    # API client, types
    App.tsx
  index.html
  tailwind.config.ts
```

## Phased Milestones

Check items off as you complete them (`- [ ]` → `- [x]`). Each phase ends with its own **Verify** items — don't check the phase "done" mentally until those pass too.

### Phase 0 — Setup & data
- [ ] `uv add sentence-transformers chromadb rank-bm25 pymupdf beautifulsoup4 groq python-dotenv` (SQLite needs no extra dep — stdlib `sqlite3`)
- [ ] Create `.env` with `GROQ_API_KEY`
- [ ] Create `.gitignore`: `.venv`, `data/raw`, `data/processed`, `data/chroma`, `data/app.db`, `.env`
- [ ] Create SQLite registry schema — `documents` table (id, title, type, status, chunk_count)
- [ ] Write `fetch_edgar_contracts.py`; pull ~5–10 sample contracts into `data/raw/`
- [ ] Write `fetch_courtlistener_cases.py`; pull ~5–10 sample case opinions into `data/raw/`
- [ ] Write `fetch_statutes.py`; pull ~5–10 sample statutes into `data/raw/`
- [ ] Call the Groq API end-to-end on one short doc and confirm a real completion comes back
- [ ] Run the embedding model on one short doc and confirm the output vector shape/dimension
- [x] Scaffold `frontend/` with Vite + React + TypeScript + Tailwind CSS
- [ ] **Verify:** all three fetch scripts produce non-empty files in `data/raw/`
- [ ] **Verify:** a one-off test script embeds one doc and checks the vector dimension matches the model's expected size

### Phase 1 — Naive baseline (deliberately bad, on purpose)
- [ ] Implement `loaders.py` — PDF/HTML/text → raw text per doc type
- [ ] Implement `chunker.py` fixed-size mode — split raw text into naive equal-size windows, no structure awareness
- [ ] Implement `embedder.py` — `sentence-transformers` wrapper
- [ ] Implement `vector_store.py` — Chroma wrapper (add/query chunks)
- [ ] Implement `scripts/ingest.py` — chunk → embed → store in Chroma, register doc in SQLite (id, title, type, status, chunk_count)
- [ ] Run `ingest.py` on the first sample doc end-to-end
- [ ] Implement `/summarize` endpoint — vector-only retrieval, single prompt, no citations
- [ ] Build **Library** page — list docs from the SQLite registry
- [ ] Build bare **Document view** — question in, plain summary text out
- [ ] **Verify:** run `ingest.py` then hit `/summarize` — returns a result with no errors
- [ ] **Verify:** note and write down one obviously bad chunk/answer (wrong clause pulled, mid-sentence cut, doc too long) as the documented baseline weakness

### Phase 2 — Structural chunking
- [ ] Build `structure_parser.py` rules for contracts (`1.1` / `Article X` numbering)
- [ ] Build `structure_parser.py` rules for statutes (`§` numbering)
- [ ] Build `structure_parser.py` rules for case law (paragraph markers)
- [ ] Define the `Document > Section > Clause` tree data model
- [ ] Implement the structural chunker — split at clause/section boundaries using the parsed tree
- [ ] Handle tiny clauses — merge into neighbors
- [ ] Handle oversized clauses — fall back to sentence-level splitting
- [ ] Attach `section_id`, `heading`, `doc_id` metadata to every chunk (this is what citation uses later)
- [ ] Detect cross-references at minimum (e.g. "as defined in Section 3.2") — just detect, don't resolve
- [ ] *(Stretch)* Resolve detected cross-references to their target clause
- [ ] Re-ingest the Phase 1 sample doc through the new structural chunker
- [ ] **Verify:** dump the chunk tree for the sample doc and confirm chunk boundaries line up with the real section/clause boundaries by eye

### Phase 3 — Grounded citation
- [ ] Write `prompts.py` — citation-aware prompt template instructing the model to cite only given chunk ids inline (e.g. `[§4.2(b)]`)
- [ ] Wire the prompt template into the query/summarize flow, passing retrieved chunk ids
- [ ] Implement `citation_validator.py` — post-hoc check that every citation in the model's output maps to an actually-retrieved chunk
- [ ] Flag or strip citations that don't validate
- [ ] Update **Document view** — render the summary with inline citations linked to the matching source text
- [ ] Add a Markdown export button (summary + citations)
- [ ] **Verify:** manually check every citation in one sample summary against the shown source text
- [ ] **Verify:** deliberately inject a bad/fabricated citation and confirm the validator catches it

### Phase 4 — Retrieval quality eval
- [ ] Implement `keyword_store.py` — BM25 wrapper
- [ ] Implement `hybrid.py` — Reciprocal Rank Fusion of vector + BM25 results
- [ ] Implement `reranker.py` — cross-encoder rerank of the fused results
- [ ] Hand-build `golden_set.json` — ~30–50 question → expected-clause-id pairs across a few docs
- [ ] Implement `retrieval_eval.py` — precision@k, recall@k, MRR
- [ ] Add a citation-accuracy metric to the eval
- [ ] Implement `run_eval.py` — CLI to run a pipeline config against the golden set and print metrics
- [ ] Record baseline metrics: naive vector-only retrieval
- [ ] Record metrics: + hybrid (vector + BM25)
- [ ] Record metrics: + reranker
- [ ] Build **Inspector** page — per-chunk vector/BM25/rerank scores, highlighted in the document
- [ ] Build **Eval dashboard** page — render `run_eval.py` output as a table/chart
- [ ] **Verify:** eval numbers actually improve naive → hybrid → hybrid+rerank; if not, investigate before moving on

### Phase 5 — Long-context handling
- [ ] Implement naive truncate-and-stuff summarization strategy
- [ ] Implement map-reduce strategy — summarize each section, then combine
- [ ] Implement refine strategy — running summary updated section by section
- [ ] Pick one genuinely long document, long enough to overflow a **self-imposed** context budget (e.g. ~4k tokens) — see [TECH_STACK.md](./TECH_STACK.md#why-these-over-the-obvious-alternatives): Groq's real chat models turned out to all have ~131k-token windows, so we cap the naive strategy's input ourselves rather than relying on the provider's actual limit
- [ ] Run all three strategies on that document
- [ ] Compare quality, latency, and cost across the three, side by side
- [ ] Build **Compare** page — same query, two configs, results side by side
- [ ] **Verify:** save all three strategies' outputs side by side and review where the naive one loses information

### Phase 6 — Stretch / polish
- [ ] Frontend polish pass — component cleanup
- [ ] Add loading/error states throughout the frontend
- [ ] Responsive layout pass
- [ ] *(Optional)* migrate to pgvector, compare against Chroma
- [ ] Write a `docker-compose.yml` for reproducibility
- [ ] Deploy backend + frontend to free hosts (Render/Fly.io/Vercel)
- [ ] **Verify:** confirm the chosen free host gives a persistent volume (not ephemeral storage) for `data/chroma` and `data/app.db`, or they reset on every redeploy

## Pitfalls to watch for
- Don't tune chunk size by eye — use the eval harness (Phase 4) once it exists.
- Groq's free tier is rate-limited and shared across all visitors once live — add the per-IP rate limit (Phase 1/6) before that matters, not after.
- Keep `GROQ_API_KEY` out of git (`.env` + `.gitignore`, from Phase 0).
- Treat document text as untrusted input to the LLM — prompt injection via document content is a real, teachable risk here.
- Reset or version Chroma's persistence directory when the chunking strategy changes, or you'll query stale chunks.
- SQLite and Chroma are both just files on disk — when deploying (Phase 6), confirm the free host gives a persistent volume, not ephemeral storage, or both reset on every redeploy.

