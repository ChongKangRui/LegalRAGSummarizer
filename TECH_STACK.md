# Tech Stack

Everything here is free — no paid APIs, no paid infra.

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI + `uv` | Already scaffolded; Python fits the ML ecosystem. |
| Embeddings | `sentence-transformers` (`BAAI/bge-small-en-v1.5`), local | Free, no API key, light enough to deploy anywhere. |
| Generation LLM | Groq free tier, `openai/gpt-oss-20b` (OpenAI-compatible API) | Free and fast. *(Updated Aug 2026: checked live against the account's actual `/models` list — Groq's real chat models are now all ~131k-token context, not the 8k–32k assumed below. See the long-context note under "Why these" — we now impose our own smaller context budget for Phase 5 instead of relying on the model's real limit.)* |
| Vector store | Chroma (embedded, file-based) | No server to run, no Postgres decision needed yet. |
| Keyword search | `rank_bm25` (pure Python) | Simplest way to add real hybrid search (BM25 + vector) without extra infra. |
| Reranker | local cross-encoder (`ms-marco-MiniLM-L-6-v2`) | Free, local, the standard second-stage retrieval step. |
| Doc parsing | `pymupdf` (PDF), `beautifulsoup4` (HTML) | Covers contracts, statutes, and ToS/privacy pages. |
| Eval | plain Python scripts | Precision/recall/MRR + citation accuracy; too small to need a framework. |
| Frontend | React/TailwindCss | 
| App state | SQLite (single file) | Not vector data, so it doesn't belong in Chroma: the document registry (title, type, status) and rate-limit counters for the live app. Free, zero infra, unrelated to the pgvector/Postgres decision above. |

## Why these, over the obvious alternatives
- **Hand-rolled, not LangChain/LlamaIndex** — a framework would own exactly the parts (chunking, retrieval scoring, citations) this project exists to teach.
- **Groq, not Ollama** — Ollama needs a beefy always-on server to deploy. With Groq the LLM runs on their infra, so your backend can deploy anywhere for free.
- **Groq, not Gemini** — Gemini's 1M-token window is so large you'd rarely hit a real context limit. Originally we expected Groq's smaller models to hit a real limit organically instead; checking the live model list showed that's no longer true (Groq's current general-purpose chat models — `openai/gpt-oss-20b`/`120b`, `qwen/qwen3.6-27b`, etc. — are ~131k tokens too, same ballpark as everyone else's flagship models now). So for Phase 5 we impose our own smaller context budget (e.g. pretend the limit is ~4k tokens) rather than relying on the provider's real one — still teaches the same lesson (naive truncation loses information; map-reduce/refine don't), and mirrors a real practice: even huge-context models degrade on long inputs ("needle in a haystack"), so production systems budget context deliberately anyway.
- **Chroma, not pgvector** — no need to commit to Postgres yet. pgvector is a good optional exercise later, once the RAG basics are solid.

## Data sources (free, real legal text, in bulk)
- **SEC EDGAR** exhibit filings (`EX-10`) — real contracts (leases, licensing, employment, M&A), free and bulk-downloadable. Most people don't know these exist.
- **CourtListener / RECAP** — case law opinions, free bulk API.
- **govinfo.gov / Cornell LII** — US Code, CFR, statutes.
- **ToS;DR** — ready-made ToS/privacy-policy text, good for early testing.
