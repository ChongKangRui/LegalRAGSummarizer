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

No login and no per-user data — but "no files at all" isn't quite right. Going public just needs a little more, still with zero accounts:

- **Corpus vectors on disk** — the deployed retrieval path reads a precomputed `data/vectors.npy` (+ `vectors.meta.json`) written by `ingest.py`; brute-force numpy over it, no vector server. Chroma is a local/large-library option, not required to go live — see [Deployment](#deployment-embedding-backend--memory-budget).
- **Document registry (SQLite)** — the Library page needs a clean list of documents (title, type, status). Reconstructing that from the per-chunk metadata works but is awkward; a small table is simpler.
- **Rate limiting (SQLite or in-memory, per IP)** — once it's public, everyone shares one Groq free-tier quota. Without a request cap, one visitor can exhaust it for everyone else. This becomes a requirement at launch, not a nice-to-have.
- **Curated library only, no public upload** — the app decided against letting visitors upload their own documents. That avoids storing strangers' files, per-visitor cleanup, and a much bigger upload-abuse surface — you control what's in the library by running the ingest scripts yourself.

See [TECH_STACK.md](./TECH_STACK.md) for where SQLite fits alongside Chroma.

## Deployment: embedding backend & memory budget

Local embeddings are the Phase 0 default, but on a small host the model *runtime* dominates
RAM, not the model weights. Measured peak RSS (`/usr/bin/time -v`, the
`four_structural_chunk.py` pipeline, `bge-small-en-v1.5`):

| Backend | Peak RSS | Cold start | Notes |
|---|---|---|---|
| `sentence-transformers` + `torch` (CPU) | ~1.5 GB | ~12 s | `torch` is ~99% of it; OOMs a 512 MB host |
| `fastembed` (quantized ONNX, no torch) | ~235 MB | ~7 s first run / ~1 s warm | same `bge-small-en-v1.5`, identical top-k ranking; whole app ≈ 300–350 MB → fits 512 MB (see the component budget below) |
| HuggingFace Inference API (no local model) | ~FastAPI baseline (~100 MB) | n/a | fallback if the box can't hold ~330 MB — free serverless `feature-extraction`, but rate-limited and adds network latency + an external dependency |

**Decision:** anything deployed uses `fastembed`. Escalate to the HF Inference API only if
the measured RSS on the target host still exceeds its RAM.

`embedder.py` becomes a provider adapter (mirroring `llm_client.py`): `fastembed` (default)
| ~~`sentence-transformers`~~ (local-only) | `hf-api`, chosen by config, one interface
(`embed(texts) -> np.ndarray`, L2-normalized).

### Fitting 512 MB / 0.1 CPU — realistic deploy rules

The ~235 MB above is the embedder *alone*. The whole running app adds the web server, the
vector index, and BM25 on top. Component budget at steady state:

| Component | RAM |
|---|---|
| Python + uvicorn + FastAPI, **1 worker** | ~60–90 MB |
| `fastembed` (bge-small quantized, resident) | ~150–200 MB |
| Vector index | numpy `.npy`: ~2–10 MB **·** Chroma (HNSW held in RAM): ~80–150 MB |
| BM25 (`rank_bm25`, tokenised corpus) | ~10–40 MB |
| Groq client | ~13 MB (HTTP only — the LLM runs on Groq) |
| Per-request working set (embed 1 query, build JSON) | single-digit MB |

Three rules keep the total near **~300–350 MB** instead of ~450–500:

1. **One uvicorn worker** (`--workers 1`). Every extra worker multiplies the whole table,
   and 0.1 CPU can't drive more than one anyway. Requests serialise — fine for a
   low-traffic portfolio app, not for real concurrency.
2. **Precompute corpus embeddings offline.** `ingest.py` writes vectors to disk; the web
   process only ever embeds the *query* — one short string, ~150–300 ms on 0.1 CPU — never
   a batch. PDF parsing and chunking also stay in the offline script, never the request
   path.
3. **Skip Chroma for the small curated library.** Store precomputed vectors as one `.npy`
   (plus a parallel list of chunk metadata) and brute-force cosine — `V @ q`, `argsort` —
   which is microseconds for a few thousand chunks and ~2–10 MB. Chroma's HNSW index and
   dependency tree only earn their ~100 MB past ~10k vectors or when server-side metadata
   filtering is needed. Make `vector_store.py` an adapter: `numpy` backend (default, deploy)
   / `chroma` backend (local, learning, large libraries).

**0.1 CPU:** model load takes ~10 s — hide it behind a startup warmup, not the first
request. Query embedding is ~150–300 ms; retrieval (`@` + `argsort`) is negligible; the
Groq generation call is network-bound and uses no local CPU. If the host enforces 0.1 as a
hard cap, expect throttled bursts and spiky tail latency — acceptable for a demo.

### `sentence-transformers` — retained, struck through, not deleted

It produced the A/B comparison above and stays useful for re-running it, so it is **kept**,
just demoted: `uv add --group experiments sentence-transformers` moves it (and `torch`) into
a local-only dependency group. It is never a runtime dep; the production image installs
neither. Keeping it *installed locally* costs **no RAM** — the cost is paid at `import`, not
install — only image size (~200 MB `torch` wheel), dependency-resolution time, and the risk
of an accidental transitive import, all of which the dependency group avoids for deploys.
The same applies to the Phase 4 reranker: use `fastembed`'s `TextCrossEncoder`
(`ms-marco-MiniLM-L-6-v2`, ONNX) so a `sentence-transformers` `CrossEncoder` doesn't pull
the whole stack back in.

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
      embedder.py             # provider adapter: fastembed (default) / sentence-transformers / hf-api
    retrieval/
      vector_store.py         # adapter: numpy (.npy brute-force, default/deploy) / chroma (local, large)
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
    vectors.npy     # precomputed corpus embeddings for the numpy backend (gitignored)
    vectors.meta.json  # parallel chunk metadata (section_id, doc_id, text) (gitignored)
    chroma/         # Chroma persistence dir — only if the chroma backend is used (gitignored)
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
- [x] `uv add fastembed rank-bm25 pymupdf beautifulsoup4 groq python-dotenv` + `uv add --group experiments sentence-transformers chromadb` (SQLite needs no extra dep — stdlib `sqlite3`) — _partial: `fastembed`, `groq`, `python-dotenv`, `beautifulsoup4`, `fastapi` in as runtime deps; `sentence-transformers` removed outright (not demoted to `experiments` as originally planned); `chromadb` added as a **plain runtime dep**, not the `experiments` group — reconcile against [Deployment](#deployment-embedding-backend--memory-budget), which calls for numpy-brute-force as the default and Chroma as opt-in. Still missing: `rank-bm25`, `pymupdf`_
- [x] Create `.env` with `GROQ_API_KEY`
- [x] Create `.gitignore`: `.venv`, `data/raw`, `data/processed`, `data/chroma`, `data/app.db`, `.env`
- [ ] Create SQLite registry schema — `documents` table (id, title, type, status, chunk_count)
- [x] ~~Write `fetch_edgar_contracts.py` / `fetch_courtlistener_cases.py` / `fetch_statutes.py`~~ — **dropped.** Automated fetchers aren't worth building for a *curated* library that changes a few times a year. Each source needs its own scraper, breaks when the site changes, and teaches scraping rather than RAG. Documents are sourced by hand instead: `curl` the page, then check it actually parses (`CLAUSE_RE` match count, preamble size, max chunk size) before keeping it — the check is the part that matters, not the download. Current corpus: 8 docs / 841 chunks in `backend/documents/` (foodpanda, shopee, atlassian, gitlab, netflix, linkedin, grab, airbnb)
- [x] Call the Groq API end-to-end on one short doc and confirm a real completion comes back — _spike: `scripts/zero_check_setup.py`_
- [x] Run the embedding model on one short doc and confirm the output vector shape/dimension — _spike: `scripts/two_embed_similarity.py`, `bge-small-en-v1.5` → 384-dim_
- [x] Scaffold `frontend/` with Vite + React + TypeScript + Tailwind CSS
- [x] **Verify:** every document in `backend/documents/` actually parses before it's kept — _the replacement for the dropped fetch-script verify. Candidates are curl'd, run through `loader` + `CLAUSE_RE`, and rejected unless they yield ≥15 clean `X.Y` matches with a small preamble. ~15 major-brand ToS were tested; **10 failed** — Spotify, Discord, Dropbox, PayPal, Amazon, eBay, Microsoft, TikTok, Twitch, Cloudflare all returned 0 matches (JS-rendered, or prose under non-numbered headings), and Zoom/Lazada/Uber/Wise returned essentially no text at all. Only Netflix, LinkedIn, Grab and Airbnb passed_
- [x] **Verify:** a one-off test script embeds one doc and checks the vector dimension matches the model's expected size — _`scripts/two_embed_similarity.py` prints `(384,)`_

### Phase 1 — Naive baseline (deliberately bad, on purpose)
- [x] ~~Implement `loaders.py` — PDF/HTML/text~~ → **scoped to HTML only.** `app/ingestion/loader.py` (BeautifulSoup, prefers `<main>`/`<article>`) covers the whole corpus. PDF and plain-text support is **dropped**: every document that survived the Phase 0 parse check is a scraped HTML page, `pymupdf` would add a dependency nothing uses, and PDF extraction is its own rabbit hole (column detection, ligatures, no clause structure) that teaches parsing rather than RAG. Revisit only if a must-have document turns out to be PDF-only
- [x] Implement `chunker.py` fixed-size mode — split raw text into naive equal-size windows, no structure awareness — _now a real module: `app/ingestion/chunker.py::naive_chunk`, kept as the Phase 4 eval control, not just the spike_
- [x] Implement `embedder.py` — embedding provider adapter — _`app/embedding/embedder.py` wraps `fastembed`'s `bge-small-en-v1.5`: `embed_documents` (passage) / `embed_question` (query, BGE prefix), lazy-loaded via `@cache`. `fastembed` confirmed at ~235 MB peak RSS vs `sentence-transformers` ~1.5 GB; `sentence-transformers` since removed from deps entirely_
- [x] Implement `vector_store.py` — **adapter complete; both backends built and verified equivalent.** `vector_store.py` is now a thin façade reading `VECTOR_BACKEND` (env, default `chroma`) and dispatching to `chroma_store.py` or `numpy_store.py`. Both implement the same six functions with backend-neutral shapes (`query` → `list[dict]` carrying a `score`, higher = better; Chroma's cosine *distance* flipped to `1 - d` so it matches numpy's raw dot product). Verified identical: same 742 count, same top-3 sections, same scores to 4 decimals across several questions. numpy persists `data/vectors.npy` (1.1 MB) + `data/vectors.meta.json` (0.7 MB) against Chroma's ~70 MB resident — switching is one env var, and the two stores coexist on disk
- [x] Implement `scripts/ingest.py` — _`script/ingest.py`: loader → chunker → embedder → Chroma `insert` over the whole corpus (skips `statute-*`); SQLite doc registration still not implemented_
- [x] Run `ingest.py` on the first sample doc end-to-end — _done, and beyond: ran on the full 4-doc curated corpus; `count()` confirmed to match total chunks inserted_
- [x] Implement `/summarize` endpoint — vector-only retrieval, single prompt, no citations — _`app/api/summarization.py`: `POST /summarize` (embed question → Chroma `query` scoped by `where={"doc_id": …}` → Groq → `SummaryResponse`) **plus** `POST /summarize/stream`, an SSE variant yielding `{"type":"token"}` frames then a final `{"type":"done"}` frame carrying citations/strategy/latency (streaming can't return a JSON body, so the metadata rides the last event). `citations` is `[]` and `strategy` is echoed — both stubs until Phases 3/5_
- [x] Build **Library** page — list docs from the SQLite registry — _page works against a real `GET /documents`, but **not from SQLite**: `app/api/documents.py` derives the list from Chroma metadata (`doc_chunk_counts()`), with `title`/`type` de-slugged from the `doc_id` and `ingestedAt` from the source file's mtime. `source` is stubbed `""` — a real registry is still the Phase 0 item above_
- [x] Build bare **Document view** — question in, plain summary text out — _`DocumentPage.tsx` on real data: `GET /documents/{id}` returns a `DocumentDetail` with a synthetic `Section > Clause` tree (flat chunks grouped by the leading number of `section_id`), and the Ask box streams tokens live via `queryApi.summarizeWithStream` (fetch + `getReader()` + SSE frame parsing; axios buffers, so it can't be used here)_
- [x] **Verify:** run `ingest.py` then hit `/summarize` — returns a result with no errors — _verified end to end from the browser, and answers spot-checked against the source: "which law governs / where are disputes heard" returned Atlassian §20.4's two branches (Ireland for EMEA, California + San Francisco courts elsewhere) with nothing invented or dropped_
- [x] **Verify:** note and write down one obviously bad chunk/answer (wrong clause pulled, mid-sentence cut, doc too long) as the documented baseline weakness — _found: clause 4.1 split across chunks 3+4; wrong clause (4.2(b)) ranked #1; `top_k=1` → Groq says "60 days". Analysis in this session; still to be committed to a docstring/README._

### Phase 2 — Structural chunking
- [x] Build `structure_parser.py` rules for contracts (`1.1` / `Article X` numbering) — _two patterns, merged and position-sorted, zero collisions across the corpus: `CLAUSE_RE` for `1.1` / `1.1.4` / `4.2(b)` (three levels — Grab needs it, and the size guards below are what stop it shredding foodpanda's list items), and `HEADING_RE` for bare `8. Title` section headings. The heading pattern uses a lookahead `(?=[A-Z])` rather than consuming the capital — consuming it made `m.end()` land one char late and ate the title's first letter (`Software` → `oftware`). Effect: chunks containing a different section's heading went **185 → 0**; Atlassian §7.2 no longer swallows sections 8, 9 and 10. `Article X` still not started_

- [x] Define the `Document > Section > Clause` tree data model — _still a flat `list[dict]`, not a tree_
- [x] Implement the structural chunker — split at clause/section boundaries using the parsed tree — _`app/ingestion/chunker.py::structural_chunk`: regex boundary split, duplicate `section_id`s disambiguated so `chunk_id`s stay unique; flat list, no tree yet; now a real module run over the whole corpus via `script/ingest.py`, not just the spike_
- [x] Handle tiny clauses — merge into neighbors — _a fragment merges into its **parent** only (`sid.startswith(parent + ".")`), never a sibling: absorbing a sibling would leave a chunk labelled §1.1.5 that actually contains §1.1.6's text, making its citation wrong. Orphans with no parent stay standalone rather than being mislabelled. Separately, `MIN_CHUNK_SIZE = 40` drops titles with no body — Grab's 12% table-of-contents was generating a chunk per index line (`"Payments"`, `"Definitions"`): micro-chunks **224 → 1**_
- [x] Handle oversized clauses — fall back to sentence-level splitting — _threshold measured, not guessed: 512 tokens is 1471–2518 chars on this corpus, so `OVERSIZE_CLAUSE_SIZE = 1400` stays under the worst case. Greedy packing on `\n` then `. ` (the loader strips blank lines, so `\n` is the coarsest break; measured: no single sentence exceeds the limit, so no character-level fallback is needed). `pack` will not flush a buffer still under `MIN_CHUNK_SIZE` — otherwise a heading line followed by a long body became its own 28-char piece, orphaning the title from the text it introduces. Oversized chunks **93 → 0**; the ~19% of corpus text that was past the embedding cutoff is now reachable_
- [x] Attach `section_id`, `heading`, `doc_id` metadata to every chunk (this is what citation uses later) — _partial: `section_id` and `doc_id` attached and verified in both stores; split pieces carry `part` and share the parent's `section_id`, so `[§1.1]` stays valid whichever piece the model read. `heading` still not captured — the Document view therefore renders "Section 14" instead of the real title, and citations have no human-readable label_
- [x] Detect cross-references at minimum (e.g. "as defined in Section 3.2") — just detect, don't resolve
- [x] *(Stretch)* Resolve detected cross-references to their target clause
- [x] Re-ingest the Phase 1 sample doc through the new structural chunker — _done, and beyond: the whole curated corpus goes through `structural_chunk` into Chroma via `script/ingest.py`_
- [x] **Verify:** dump the chunk tree for the sample doc and confirm chunk boundaries line up with the real section/clause boundaries by eye — _8 clauses, boundaries match; clause 4.1 goes from split-across-ranks-2/3 to retrieved whole at rank 1_

### Phase 3 — Grounded citation
- [x] Write additional prompt — citation-aware prompt template instructing the model to cite only given chunk ids inline (e.g. `[§4.2(b)]`)
- [x] Wire the prompt template into the query/summarize flow, passing retrieved chunk ids
- [x] Implement `citation_validator.py` — post-hoc check that every citation in the model's output maps to an actually-retrieved chunk
- [x] Flag or strip citations that don't validate
- [x] Update **Document view** — render the summary with inline citations linked to the matching source text
- [x] Add a Markdown export button (summary + citations)
- [x] **Verify:** manually check every citation in one sample summary against the shown source text
- [x] **Verify:** deliberately inject a bad/fabricated citation and confirm the validator catches it

### Phase 4 — Retrieval quality eval
- [x] Implement `keyword_store.py` — BM25 wrapper
- [x] Implement `hybrid.py` — Reciprocal Rank Fusion of vector + BM25 results
- [x] Implement `reranker.py` — cross-encoder rerank of the fused results via `fastembed` `TextCrossEncoder` (`ms-marco-MiniLM-L-6-v2`, ONNX), not a `sentence-transformers` `CrossEncoder` (drags `torch` back in — see [Deployment](#deployment-embedding-backend--memory-budget))
- [x] Hand-build `golden_set.json` — ~30–50 question → expected-clause-id pairs across a few docs
- [x] Implement `retrieval_eval.py` — precision@k, recall@k, MRR
- [x] Add a citation-accuracy metric to the eval
- [x] Implement `run_eval.py` — CLI to run a pipeline config against the golden set and print metrics
- [x] Record baseline metrics: naive vector-only retrieval
- [x] Record metrics: + hybrid (vector + BM25)
- [x] Record metrics: + reranker
- [x] Build **Inspector** page — per-chunk vector/BM25/rerank scores, highlighted in the document
- [x] Build **Eval dashboard** page — render `run_eval.py` output as a table/chart
- [x] **Verify:** eval numbers actually improve naive → hybrid → hybrid+rerank; if not, investigate before moving on. **It is worth to mention here that the reason hybrid become the least score in the eval test can be read at keyword_store.py. Keyword_store.py is the real root cause.**

### Phase 5 — Long-context handling
- [x] Implement naive truncate-and-stuff summarization strategy
- [x] Implement map-reduce strategy — summarize each section, then combine
- [x] Implement refine strategy — running summary updated section by section
- [x] Combine vector, hybrid(bm25 + vector) and rerank as part of the options for ask section. Total of 6 options allow for choosen.
- [x] Due to limitation of free AI api request, naive, map-reduce and refine will be removed from deployed version. It should controlled based on the .env  **ENABLE_LARGE_ANSWER_STRATEGY**.
- [x] Pick one genuinely long document, long enough to overflow a **self-imposed** context budget (e.g. ~4k tokens) — see [TECH_STACK.md](./TECH_STACK.md#why-these-over-the-obvious-alternatives): Groq's real chat models turned out to all have ~131k-token windows, so we cap the naive strategy's input ourselves rather than relying on the provider's actual limit
- [x] Run all three strategies on that document
- [x] Compare quality, latency, and cost across the three, side by side
- [x] Build **Compare** page — same query, two configs, results side by side
- [x] **Verify:** save all three strategies' outputs side by side and review where the naive one loses information

### Phase 6 — Stretch / polish
- [] Add rate limiting
- [x] Frontend polish pass — component cleanup
- [x] Add loading/error states throughout the frontend
- [x] Responsive layout pass
- [ ] Write a `docker-compose.yml` for reproducibility
- [x] Move `sentence-transformers` (+ `torch`) and `chromadb` into the `experiments` dependency group (`uv add --group experiments ...`); confirm the production image installs none of them — see [Deployment: embedding backend & memory budget](#deployment-embedding-backend--memory-budget)
- [x] Confirm the deployed embedding backend is `fastembed` (quantized ONNX), and bake the model into the image (or accept a one-time ~7 s first-request download)
- [x] Confirm `vector_store.py` runs its `numpy` backend in deploy (precomputed `.npy`), not Chroma; `ingest.py` / PDF parsing run offline only
- [ ] Deploy with a **single uvicorn worker** (`--workers 1`); warm up the embedding model on startup, not the first request
- [ ] Deploy backend + frontend to free hosts (Railway/Vercel)
- [ ] **Verify:** measure peak RSS on the target host under a real query; target ~300–350 MB. If it exceeds the host's RAM, switch `embedder.py` to the `hf-api` provider
- [ ] **Verify:** confirm the chosen free host gives a persistent volume (not ephemeral storage) for `data/` (the `.npy` vectors + `app.db`, and `data/chroma` if used), or they reset on every redeploy

## Pitfalls to watch for
- Don't tune chunk size by eye — use the eval harness (Phase 4) once it exists.
- Groq's free tier is rate-limited and shared across all visitors once live — add the per-IP rate limit (Phase 1/6) before that matters, not after.
- Keep `GROQ_API_KEY` out of git (`.env` + `.gitignore`, from Phase 0).
- Treat document text as untrusted input to the LLM — prompt injection via document content is a real, teachable risk here.
- Reset or version Chroma's persistence directory when the chunking strategy changes, or you'll query stale chunks.
- Local embedding RAM is dominated by the model *runtime*, not the model — `sentence-transformers` + `torch` peaks at ~1.5 GB. Deploy with `fastembed` (quantized ONNX, ~235 MB); keep `torch` out of the production image. See [Deployment: embedding backend & memory budget](#deployment-embedding-backend--memory-budget).
- Every uvicorn/gunicorn worker loads its own copy of the embedder — on a 512 MB host, `--workers 2` roughly doubles RAM and OOMs. Deploy with `--workers 1`.
- The `fastembed` model downloads on first use (~7 s). Without a startup warmup that latency lands on a real user's first request, and on a read-only container the download can fail outright — bake the model into the image or warm it in a lifespan hook.
- Don't run ingestion (PDF parse + batch embed) inside the web process — `pymupdf` and batch encoding spike memory well past the steady-state budget. Keep it in `scripts/ingest.py`, run offline.
- SQLite and Chroma are both just files on disk — when deploying (Phase 6), confirm the free host gives a persistent volume, not ephemeral storage, or both reset on every redeploy.

