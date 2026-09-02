# Tech Stack

Everything here is free — no paid APIs, no paid infra.

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI + `uv` | Already scaffolded; Python fits the ML ecosystem. |
| Embeddings | ~~`sentence-transformers` (`BAAI/bge-small-en-v1.5`), local~~ → **`fastembed`** — same `BAAI/bge-small-en-v1.5`, quantized ONNX, local | ~~"light enough to deploy anywhere"~~ was wrong: `sentence-transformers` pulls `torch` (~1.5 GB peak RSS, ~200 MB wheel) and OOMs a 512 MB host. `fastembed` runs the *same* model on `onnxruntime` at ~235 MB with identical top-k ranking. `sentence-transformers` kept in a local-only dep group for the A/B comparison. See [Deploying on a 512 MB host](#deploying-on-a-512-mb-host). |
| Generation LLM | Groq free tier, `openai/gpt-oss-20b` (OpenAI-compatible API) | Free and fast, and the LLM runs on Groq's infra so it adds ~13 MB (just an HTTP client) to the backend's RAM. *(Updated Aug 2026: checked live against the account's actual `/models` list — Groq's real chat models are now all ~131k-token context, not the 8k–32k assumed below. See the long-context note under "Why these" — we now impose our own smaller context budget for Phase 5 instead of relying on the model's real limit.)* |
| Vector store | ~~Chroma (embedded, file-based)~~ → **precomputed `.npy` + brute-force numpy** for the curated library; Chroma optional (local, or once the library passes ~10k chunks) | The curated library is small (a few thousand chunks). Chroma's in-RAM HNSW index + dependency tree cost ~80–150 MB for no ranking gain at that size; `numpy` `V @ q` + `argsort` is microseconds and ~2–10 MB, and it's more transparent for learning. `vector_store.py` is an adapter — `numpy` (default, deploy) / `chroma` (local, large). See [Deploying on a 512 MB host](#deploying-on-a-512-mb-host). |
| Keyword search | `rank_bm25` (pure Python) | Simplest way to add real hybrid search (BM25 + vector) without extra infra. Holds the tokenised corpus in memory (~10–40 MB for the curated library). |
| Reranker | ~~local cross-encoder (`ms-marco-MiniLM-L-6-v2`) via `sentence-transformers`~~ → **`fastembed` `TextCrossEncoder`** (same `ms-marco-MiniLM-L-6-v2`, ONNX) | A `sentence-transformers` `CrossEncoder` drags the whole ~1.5 GB `torch` stack back in. `fastembed`'s `TextCrossEncoder` reranks with the same model on the `onnxruntime` that's already loaded for embeddings. If RAM is still tight at deploy, make reranking deploy-optional (Phase 4 eval still runs it locally). |
| Doc parsing | `pymupdf` (PDF), `beautifulsoup4` (HTML) | Covers contracts, statutes, and ToS/privacy pages. |
| Eval | plain Python scripts | Precision/recall/MRR + citation accuracy; too small to need a framework. |
| Frontend | React/TailwindCss | 
| App state | SQLite (single file) | Not vector data, so it doesn't belong in Chroma: the document registry (title, type, status) and rate-limit counters for the live app. Free, zero infra, unrelated to the pgvector/Postgres decision above. |

## Why these, over the obvious alternatives
- **Hand-rolled, not LangChain/LlamaIndex** — a framework would own exactly the parts (chunking, retrieval scoring, citations) this project exists to teach.
- **Groq, not Ollama** — Ollama needs a beefy always-on server to deploy. With Groq the LLM runs on their infra, so your backend can deploy anywhere for free.
- **Groq, not Gemini** — Gemini's 1M-token window is so large you'd rarely hit a real context limit. Originally we expected Groq's smaller models to hit a real limit organically instead; checking the live model list showed that's no longer true (Groq's current general-purpose chat models — `openai/gpt-oss-20b`/`120b`, `qwen/qwen3.6-27b`, etc. — are ~131k tokens too, same ballpark as everyone else's flagship models now). So for Phase 5 we impose our own smaller context budget (e.g. pretend the limit is ~4k tokens) rather than relying on the provider's real one — still teaches the same lesson (naive truncation loses information; map-reduce/refine don't), and mirrors a real practice: even huge-context models degrade on long inputs ("needle in a haystack"), so production systems budget context deliberately anyway.
- **Chroma, not pgvector** — no need to commit to Postgres yet. pgvector is a good optional exercise later, once the RAG basics are solid. *(Superseded for deploy — see below: the curated library is small enough that brute-force numpy beats Chroma on RAM with no downside. Chroma stays as a local/large-library option.)*

## Deploying on a 512 MB host

`sentence-transformers` was the Phase 0 default — "free, local, light enough to deploy anywhere". The "light" part didn't survive contact with a real free tier.

Measured peak RSS (`/usr/bin/time -v`, the `four_structural_chunk.py` pipeline, same `bge-small-en-v1.5` model, same normalised-dot-product retrieval):

| Backend | Peak RSS | Cold start | Ranking on the test query |
|---|---|---|---|
| `sentence-transformers` + `torch` (CPU) | ~1.5 GB | ~12 s | clause 4.1 #1 (correct) |
| `fastembed` (quantized ONNX, no `torch`) | ~235 MB | ~7 s first run / ~1 s warm | clause 4.1 #1, score 0.83 (same) |

`torch` is ~99% of that 1.5 GB and ships as a ~200 MB wheel; a 512 MB host OOMs on import. `fastembed` runs the *same* model on `onnxruntime` with quantized weights — ~6× less RAM, ~9× faster start, identical top-k.

**Realistic deploy target: 512 MB RAM / 0.1 CPU.** The embedder is only part of the footprint. Full component budget and the rules that keep the running app near ~300–350 MB (one uvicorn worker; precompute corpus embeddings offline so the web process only embeds the query; brute-force numpy over a `.npy` instead of Chroma) are in [IMPLEMENTATION_PLAN.md → Deployment: embedding backend & memory budget](./IMPLEMENTATION_PLAN.md#deployment-embedding-backend--memory-budget).

**`sentence-transformers` is struck through, not removed.** It's the baseline half of the comparison above and worth keeping runnable. It moves to a local-only dependency group (`uv add --group experiments sentence-transformers`) — never a runtime dep, never in the production image. Keeping it *installed* locally costs no RAM (import-time cost, not install-time); the dependency group only keeps it out of deploys and off the image-size / resolution-time bill.

**Fallback** if even ~330 MB is too tight: the HuggingFace serverless Inference API (`feature-extraction` on the same model) — no local model, ~FastAPI-baseline RAM, but rate-limited and adds a network hop. `embedder.py` carries this as a third provider (`hf-api`).

## Data sources (free, real legal text, in bulk)
- **SEC EDGAR** exhibit filings (`EX-10`) — real contracts (leases, licensing, employment, M&A), free and bulk-downloadable. Most people don't know these exist.
- **CourtListener / RECAP** — case law opinions, free bulk API.
- **govinfo.gov / Cornell LII** — US Code, CFR, statutes.
- **ToS;DR** — ready-made ToS/privacy-policy text, good for early testing.
