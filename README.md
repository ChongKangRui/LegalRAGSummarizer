# LegalRAGSummarizer

A RAG system for querying and summarizing legal documents — Terms of Service, employment agreements, and commercial contracts — built to *compare* retrieval strategies against each other rather than assume one is best. Vector search, BM25 keyword search, reciprocal-rank-fusion hybrid, and cross-encoder reranking are all implemented side by side, with an eval harness that scores each one (retrieval precision/recall/MRR *and* citation accuracy) against a hand-labeled golden set — so the strategy comparison is backed by numbers, not a guess.

**Live Demo:** [legal-rag-summarizer.vercel.app](https://legal-rag-summarizer.vercel.app/)

> The backend runs on Railway's serverless tier (sleeps after idle to save resources). The **first** request after a period of inactivity will be noticeably slower than usual — the container has to wake up, then download and load the embedding and reranking models before it can answer. Subsequent requests are fast. This is expected behavior, not a bug.

---

## Features

### Retrieval

- **Structural chunking** — legal clauses are split on their own numbering scheme (`1.1`, `1.2`, `1.2.2`, etc.), not on a fixed character/token window, so a chunk boundary lines up with a clause boundary
- **Six retrieval/summarization strategies, built independently and comparable side by side**:
  - **Vector** — cosine similarity over `fastembed`-generated embeddings, stored in a hand-rolled numpy store
  - **Hybrid** — BM25 keyword search (`rank_bm25`) fused with vector search via Reciprocal Rank Fusion
  - **Hybrid + Rerank** — the hybrid candidate list re-scored by a cross-encoder (`fastembed`'s ONNX `TextCrossEncoder`) before the top-k are used
  - **Naive** — the entire document, truncated and stuffed into a single prompt with no retrieval step
  - **Map-Reduce** — the document split into groups, each summarized independently, then combined
  - **Refine** — the document processed sequentially, with the running summary refined one group at a time
  > The last three are implemented but **disabled in the live deployment** behind a feature flag (`ENABLE_LARGE_ANSWER_STRATEGY`). They require either one very large LLM call (naive) or many sequential/parallel ones (map-reduce, refine) per question — for documents like `tos-grab` (383 chunks), that exceeds Groq's free-tier token- and request-per-minute limits outright. They run fine locally with a paid tier or a smaller document.
- **Citation-aware generation** — every answer is instructed to cite the exact clause label it came from; a post-hoc validator checks each citation against what was actually retrieved and flags anything that doesn't match (a hallucinated or fabricated citation)

### Eval Harness

- **`golden_set.json`** — a hand-labeled benchmark of questions across every document in the corpus, each with its expected clause ID(s)
- **`run_eval.py`** — runs every retrieval strategy against the full golden set and reports, per strategy: precision@k, recall@k, MRR, citation validity, and citation correctness — so strategy comparisons ("does reranking actually help?") are backed by numbers, not a guess
- **Retrieval Inspector** — a per-query view showing vector, BM25, and rerank scores side by side for every candidate chunk, so you can see *why* a chunk was ranked where it was, not just the final order
- **Compare** — run multiple strategies against the same question concurrently and see the answers, citations, and latency side by side
- **Eval Dashboard** — the aggregate metrics from the latest `run_eval.py` run, rendered in the UI

### Platform / Infrastructure

- **Streaming answers (SSE)** — token-by-token generation over Server-Sent Events, with retry/backoff on rate-limit errors baked into the streaming path itself, not just the non-streaming one
- **Async throughout** — retrieval, generation, and reranking all run through `asyncio`, with CPU-bound work (BM25, cross-encoder inference) explicitly offloaded via `asyncio.to_thread` so one request's retrieval work never blocks another request's in-flight stream
- **IP-based rate limiting** — a custom FastAPI middleware, independent of (and correctly composed with) CORS
- **Process-lifetime caching** — the embedding model, reranker, BM25 index, and vector store are each loaded exactly once and kept resident for the life of the process, rather than being rebuilt per request

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, Python, `uv` (dependency management) |
| Retrieval | Custom numpy vector store, `rank_bm25`, hand-rolled Reciprocal Rank Fusion |
| Embeddings & Reranking | `fastembed` (ONNX runtime) — `BAAI/bge-small-en-v1.5` embeddings, `Xenova/ms-marco-MiniLM-L-6-v2` cross-encoder reranker |
| LLM | Groq (`openai/gpt-oss-20b` for live chat, `openai/gpt-oss-120b` for eval generation) |
| Frontend | React, TypeScript, Vite, TanStack Query, React Router |
| UI | shadcn/ui (Radix UI primitives), Tailwind CSS |
| Deployment | Railway (backend, serverless) · Vercel (frontend) |

`fastembed`'s ONNX runtime was chosen deliberately over `sentence-transformers` — it avoids pulling in `torch` as a dependency, which cuts the deployed memory footprint substantially. See `TECH_STACK.md` for the full reasoning.

**Not in the live deployment:** `chromadb` and `sentence-transformers` are kept in the project as an `experiments` dependency group — a local-only alternative retrieval/embedding path (a real vector database, and full-precision `torch`-based models) for benchmarking against the lighter `fastembed` + numpy stack, not something the deployed backend imports or runs.

---

## Project Structure

```
LegalRAGSummarizer/
├── backend/
│   ├── app/
│   │   ├── api/               # FastAPI routers — one file per resource
│   │   │   ├── summarization.py   # /summarize, /summarize/stream — the main Ask flow
│   │   │   ├── inspector.py       # /inspector — per-query retrieval score comparison
│   │   │   ├── compare.py         # /compare — multi-strategy side-by-side
│   │   │   ├── eval_dashboard.py  # /eval_dashboard — aggregate eval metrics
│   │   │   ├── documents.py       # document listing + detail
│   │   │   └── rate_limit.py      # IP-based rate limiting
│   │   ├── retrieval/
│   │   │   ├── numpy_store.py     # vector store — cosine similarity over a numpy array
│   │   │   ├── keyword_store.py   # BM25 keyword search
│   │   │   ├── hybrid.py          # Reciprocal Rank Fusion
│   │   │   ├── reranker.py        # cross-encoder reranking
│   │   │   └── truncate_and_stuff.py, map_reducer.py  # large-answer strategies
│   │   ├── embedding/
│   │   │   └── embedder.py        # question/chunk embedding
│   │   ├── generation/
│   │   │   ├── llm_client.py      # Groq client, retry/backoff, streaming
│   │   │   └── citation_validator.py  # citation extraction + validation against retrieved chunks
│   │   ├── eval/
│   │   │   ├── golden_set.json    # the benchmark
│   │   │   ├── retrieval_eval.py  # precision@k / recall@k / MRR
│   │   │   └── run_eval.py        # runs every strategy against the golden set
│   │   ├── script/
│   │   │   └── ingest.py          # document ingestion pipeline
│   │   ├── config.py, models.py, main.py
│   │   └── infra/groq_client.py
│   ├── data/                   # ingested documents + pre-built vectors (committed, not regenerated on deploy)
│   ├── Dockerfile, Dockerfile.dev
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── pages/               # DocumentPage (Ask), Inspector, Compare, Eval Dashboard
│   │   ├── hooks/queries.ts     # TanStack Query hooks — one per API resource
│   │   ├── lib/api.ts           # the API seam — every page calls through this
│   │   └── components/
│   └── Dockerfile.dev
├── docker-compose.dev.yaml     # local dev: both services, hot-reloadable from source
├── IMPLEMENTATION_PLAN.md      # phase-by-phase build plan
└── TECH_STACK.md               # stack decisions and the reasoning behind them
```

---

## Getting Started

### Prerequisites

| Tool | Needed for |
|---|---|
| [Python 3.12+](https://www.python.org/) & [uv](https://docs.astral.sh/uv/) | Backend |
| [Node.js](https://nodejs.org/) & npm | Frontend |
| [Docker](https://www.docker.com/) | Docker setup path (recommended) |
| A [Groq API key](https://console.groq.com/) | LLM generation — required for the Ask/Compare/Eval flows |

### 1. Clone the repo

```bash
git clone https://github.com/ChongKangRui/LegalRAGSummarizer.git
cd LegalRAGSummarizer
```

### 2. Set up environment variables

Copy `.env.example` to `.env` in `backend/` and fill in your Groq API key and, if running the frontend separately, `VITE_API_BASE_URL` in `frontend/`.

Now pick **one** of the two setups below.

### Option A — Docker (recommended)

One command builds and starts both the backend and frontend together, bind-mounted from source so edits hot-reload without a rebuild.

```bash
docker compose -f docker-compose.dev.yml up --build
```

- Backend → <http://localhost:8000>
- Frontend → <http://localhost:5173>

### Option B — Local machine

**Backend:**
```bash
cd backend
uv sync
uv run fastapi dev
```

**Frontend** (separate terminal):
```bash
cd frontend
npm install
npm run dev
```

---

## Ingesting Documents

The repo ships with a pre-built corpus (`backend/data/`), so ingestion isn't required to run the demo. To add or re-ingest documents yourself:

1. Place the source document as HTML under `backend/app/data/raw/` (or wherever your `documents` folder is configured — see `app/config.py`).
2. From the `backend/` folder, run:
   ```bash
   uv run app/script/ingest.py
   ```

The ingestion pipeline currently recognizes structural numbering in the form `1.1`, `1.2`, `1.2.2`, and similar patterns — clauses are chunked along those boundaries rather than a fixed character/token window. Documents that don't follow this numbering scheme won't chunk correctly.

Ingesting the full corpus takes **several minutes** (embedding generation is the slow part) — this is expected, not a hang.

---

## Running the Eval Harness

`backend/app/eval/golden_set.json` is the benchmark: a hand-labeled set of questions across every document in the corpus, each with its expected clause ID(s). To run every retrieval strategy against it and generate a fresh report:

```bash
cd backend
uv run app/eval/run_eval.py
```

This runs **vector**, **hybrid**, and **hybrid+rerank** retrieval against every question in the golden set, generates an LLM answer for each, and scores precision@k, recall@k, MRR, and citation accuracy per strategy. Because it makes real Groq API calls for every question in every strategy, it can take **several minutes** to complete, and is subject to Groq's free-tier rate limits — the script has retry/backoff built in for that.

Results are written to `EVAL_RESULT_PATH` (see `app/config.py`) and are what the Eval Dashboard page renders.

---

## Deployment

| Part | Platform |
|---|---|
| Backend | [Railway](https://railway.com) (serverless — scales to zero on idle) |
| Frontend | [Vercel](https://vercel.com) |

The backend runs with a single uvicorn worker (`--workers 1`) — the embedding model, reranker, BM25 index, and vector store are each cached for the process's lifetime, so running multiple workers would multiply memory usage without any benefit. Model weights and the pre-built vector store are committed to the repo rather than regenerated on deploy, so a fresh deploy never needs to run ingestion or re-download from Hugging Face Hub except on true cold start.

---

## What I Learned

**Retrieval & Evaluation**

- Building vector search, BM25, RRF fusion, and cross-encoder reranking from scratch (not through a framework) — and building an eval harness *before* trusting any comparison between them, since two of the real bugs caught in development (a tokenizer regex silently reducing BM25 to character-level noise, and an untruncated retriever quietly handing the LLM more context than the metrics were scored against) would have produced confident-looking but wrong conclusions about which strategy performed best
- Designing a citation-accuracy metric that's actually grounded — validating that a cited clause was *retrieved*, not just that its label happens to match the expected answer, since the latter lets a hallucinated-but-lucky citation score as "correct"

**Async & Concurrency**
 
- Why the LLM call itself had to be async, specifically: a synchronous Groq call blocks on network I/O for the whole duration of the response, and under a sync endpoint that ties up a full worker thread per in-flight request — switching to `AsyncGroq` and awaiting the call means the event loop can service other requests while waiting on the network, instead of one slow generation stalling everyone else's
- `async def` alone doesn't make a function's body non-blocking — it only helps at the points that actually `await` something. CPU-bound work (BM25 scoring, cross-encoder reranking) still runs directly on the event loop and blocks other requests unless explicitly offloaded with `asyncio.to_thread`
- Streaming LLM responses over SSE with retry/backoff on the part of the call that can actually fail (opening the stream), not the token-by-token consumption after it's already started


**Prompt Engineering**
 
- Getting a small model (20B) to reliably follow a narrow formatting rule — cite a clause label *exactly* as given, never invent a sub-part like `(a)` that isn't its own labeled chunk, and never substitute a full-width bracket for an ASCII one — took several iterations: isolating the rule into its own labeled block instead of burying it in prose, showing the specific wrong pattern next to the correct one, and rephrasing it as a literal copy instruction rather than a conditional exception. 

---

**Deployment & Cost**

- Reasoning about container memory as GB-*minutes*, not a snapshot — and using serverless scale-to-zero specifically because a demo project's real traffic pattern is mostly idle

---

## License

MIT — see [LICENSE](./LICENSE).