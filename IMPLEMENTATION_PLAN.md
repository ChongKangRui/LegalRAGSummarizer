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

> **Progress — 2026-08-30.** Phases 0–2 are being worked out first as standalone
> learning spikes in `backend/scripts/` (`zero_check_setup.py` … `four_structural_chunk.py`),
> before the reusable `backend/app/` modules. Proven end to end so far:
> - **Groq generation** — `zero_check_setup.py` gets real completions (`openai/gpt-oss-20b`).
> - **Local embeddings + vector retrieval** — `two_embed_similarity.py`: `bge-small-en-v1.5`
>   (384-dim), cosine as a normalized dot product, `argsort` top-k.
> - **Naive baseline + its documented weakness** — `one_naive_baseline.py` (200-char
>   `naive_chunk`) + `three_generate_answer.py` (retrieve → prompt → Groq). Failure found:
>   fixed-size chunks split clause 4.1 across two chunks; vector search ranks the wrong
>   clause (4.2(b), 60-day suspension) #1; at `top_k=1` Groq answers "60 days" —
>   confidently wrong. The `system` guardrail catches only *absent* info, not a
>   wrong-but-on-topic chunk.
> - **Structural chunker fixes it** — `four_structural_chunk.py`: regex splits on clause
>   labels (`^\d+\.\d+(?:\([a-z]\))?`), carries `section_id`. The same retrieval code now
>   returns clause 4.1 *whole* at rank 1; Groq then answers "30 days" correctly even at
>   `top_k=1`.
>
> **Progress — 2026-09-02.** Deployment-RAM spike for embeddings: measured
> `sentence-transformers` + `torch` at ~1.5 GB peak RSS vs `fastembed` (quantized ONNX,
> same `bge-small-en-v1.5`) at ~235 MB — identical top-k ranking on the structural clauses.
> `fastembed` added as a runtime dep; `~~sentence-transformers~~` struck as the runtime
> embedder (kept for the A/B comparison, to be demoted to an `experiments` dependency group).
> Realistic deploy target set at **512 MB / 0.1 CPU**; the plan's
> [Deployment: embedding backend & memory budget](#deployment-embedding-backend--memory-budget)
> section now carries the full component budget and three rules to hit ~300–350 MB (1 uvicorn
> worker; precompute corpus vectors offline; brute-force numpy over a `.npy` instead of
> Chroma for the small curated library). `vector_store.py` and the Phase 4 reranker updated
> to match (numpy/chroma adapter; `fastembed` `TextCrossEncoder` instead of a
> `sentence-transformers` `CrossEncoder`). Also spiked FastAPI routing/middleware in
> `backend/api/` (app-level `@app.middleware("http")` logger, `/query` `APIRouter`,
> `require_api_key` dependency) — learning scaffolding, not the real Phase 1 endpoints yet.
>
> Not yet started: `uv add chromadb rank-bm25 pymupdf beautifulsoup4`; the `backend/app/`
> modules; Chroma; the SQLite registry; the fetch/ingest scripts; the API endpoints. The
> frontend pages exist but run on mock data. The baseline-weakness analysis lives in this
> session only — still to be written into a script docstring or README.

### Phase 0 — Setup & data
- [ ] `uv add fastembed rank-bm25 pymupdf beautifulsoup4 groq python-dotenv` + `uv add --group experiments sentence-transformers chromadb` (SQLite needs no extra dep — stdlib `sqlite3`) — _partial: `fastembed`, `groq`, `python-dotenv`, `sentence-transformers` in as runtime deps; still to do: add `rank-bm25 pymupdf beautifulsoup4`, and move `sentence-transformers` (+ `chromadb` when added) to the `experiments` group per [Deployment](#deployment-embedding-backend--memory-budget). `~~sentence-transformers~~` struck as the runtime embedder — replaced by `fastembed` (see that section)_
- [x] Create `.env` with `GROQ_API_KEY`
- [ ] Create `.gitignore`: `.venv`, `data/raw`, `data/processed`, `data/chroma`, `data/app.db`, `.env`
- [ ] Create SQLite registry schema — `documents` table (id, title, type, status, chunk_count)
- [ ] Write `fetch_edgar_contracts.py`; pull ~5–10 sample contracts into `data/raw/`
- [ ] Write `fetch_courtlistener_cases.py`; pull ~5–10 sample case opinions into `data/raw/`
- [ ] Write `fetch_statutes.py`; pull ~5–10 sample statutes into `data/raw/`
- [x] Call the Groq API end-to-end on one short doc and confirm a real completion comes back — _spike: `scripts/zero_check_setup.py`_
- [x] Run the embedding model on one short doc and confirm the output vector shape/dimension — _spike: `scripts/two_embed_similarity.py`, `bge-small-en-v1.5` → 384-dim_
- [x] Scaffold `frontend/` with Vite + React + TypeScript + Tailwind CSS
- [ ] **Verify:** all three fetch scripts produce non-empty files in `data/raw/`
- [x] **Verify:** a one-off test script embeds one doc and checks the vector dimension matches the model's expected size — _`scripts/two_embed_similarity.py` prints `(384,)`_

### Phase 1 — Naive baseline (deliberately bad, on purpose)
- [ ] Implement `loaders.py` — PDF/HTML/text → raw text per doc type
- [x] Implement `chunker.py` fixed-size mode — split raw text into naive equal-size windows, no structure awareness — _spike: `scripts/one_naive_baseline.py` `naive_chunk()`; not yet the `app/` module_
- [ ] Implement `embedder.py` — embedding provider adapter (`fastembed` default; `sentence-transformers` / HF Inference API pluggable), one interface — see [Deployment: embedding backend & memory budget](#deployment-embedding-backend--memory-budget) — _spike uses `SentenceTransformer` directly in `scripts/two_embed_similarity.py`; `fastembed` proven at ~235 MB peak RSS vs ~1.5 GB, same ranking; no wrapper module yet_
- [ ] Implement `vector_store.py` — adapter: `numpy` backend (brute-force `V @ q` over a precomputed `.npy`, default + deploy) / `chroma` backend (local, or >~10k chunks) — see [Deployment](#deployment-embedding-backend--memory-budget)
- [ ] Implement `scripts/ingest.py` — chunk → embed → **write vectors + chunk metadata to disk offline** (`.npy` for the numpy backend, or Chroma), register doc in SQLite (id, title, type, status, chunk_count). Never run at request time.
- [ ] Run `ingest.py` on the first sample doc end-to-end
- [ ] Implement `/summarize` endpoint — vector-only retrieval, single prompt, no citations — _the retrieve → prompt → Groq flow exists as `scripts/three_generate_answer.py`, not an endpoint_
- [ ] Build **Library** page — list docs from the SQLite registry
- [ ] Build bare **Document view** — question in, plain summary text out
- [ ] **Verify:** run `ingest.py` then hit `/summarize` — returns a result with no errors
- [x] **Verify:** note and write down one obviously bad chunk/answer (wrong clause pulled, mid-sentence cut, doc too long) as the documented baseline weakness — _found: clause 4.1 split across chunks 3+4; wrong clause (4.2(b)) ranked #1; `top_k=1` → Groq says "60 days". Analysis in this session; still to be committed to a docstring/README._

### Phase 2 — Structural chunking
- [ ] Build `structure_parser.py` rules for contracts (`1.1` / `Article X` numbering) — _partial: `scripts/four_structural_chunk.py` regex handles `1.1` / `4.2(a)` labels; `Article X` not yet_
- [ ] Build `structure_parser.py` rules for statutes (`§` numbering)
- [ ] Build `structure_parser.py` rules for case law (paragraph markers)
- [ ] Define the `Document > Section > Clause` tree data model — _spike produces a flat `list[{section_id, text}]`, not a tree_
- [x] Implement the structural chunker — split at clause/section boundaries using the parsed tree — _spike: `scripts/four_structural_chunk.py` (regex boundary split; flat list, no tree yet)_
- [ ] Handle tiny clauses — merge into neighbors
- [ ] Handle oversized clauses — fall back to sentence-level splitting
- [ ] Attach `section_id`, `heading`, `doc_id` metadata to every chunk (this is what citation uses later) — _partial: `section_id` attached; `heading` / `doc_id` not_
- [ ] Detect cross-references at minimum (e.g. "as defined in Section 3.2") — just detect, don't resolve
- [ ] *(Stretch)* Resolve detected cross-references to their target clause
- [ ] Re-ingest the Phase 1 sample doc through the new structural chunker — _re-ran retrieval over structural chunks in the spike; no Chroma ingest yet_
- [x] **Verify:** dump the chunk tree for the sample doc and confirm chunk boundaries line up with the real section/clause boundaries by eye — _8 clauses, boundaries match; clause 4.1 goes from split-across-ranks-2/3 to retrieved whole at rank 1_

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
- [ ] Implement `reranker.py` — cross-encoder rerank of the fused results via `fastembed` `TextCrossEncoder` (`ms-marco-MiniLM-L-6-v2`, ONNX), not a `sentence-transformers` `CrossEncoder` (drags `torch` back in — see [Deployment](#deployment-embedding-backend--memory-budget))
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
- [ ] Move `sentence-transformers` (+ `torch`) and `chromadb` into the `experiments` dependency group (`uv add --group experiments ...`); confirm the production image installs none of them — see [Deployment: embedding backend & memory budget](#deployment-embedding-backend--memory-budget)
- [ ] Confirm the deployed embedding backend is `fastembed` (quantized ONNX), and bake the model into the image (or accept a one-time ~7 s first-request download)
- [ ] Confirm `vector_store.py` runs its `numpy` backend in deploy (precomputed `.npy`), not Chroma; `ingest.py` / PDF parsing run offline only
- [ ] Deploy with a **single uvicorn worker** (`--workers 1`); warm up the embedding model on startup, not the first request
- [ ] Deploy backend + frontend to free hosts (Render/Fly.io/Vercel)
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

