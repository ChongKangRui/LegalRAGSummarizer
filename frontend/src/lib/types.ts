/**
 * Domain types shared across the app.
 *
 * These mirror the pydantic models the backend will eventually expose
 * (see IMPLEMENTATION_PLAN.md -> backend/app/models.py). Keeping the shapes
 * here in sync with the backend is what lets `lib/api.ts` swap from mock
 * data to real `fetch`/axios calls without touching any page component.
 */

export type DocumentType = "statute" | "case_law" | "tos" | "contract"

export type DocumentStatus = "ready" | "processing" | "error"

export interface DocumentSummary {
  id: string
  title: string
  type: DocumentType
  status: DocumentStatus
  source: string
  chunkCount: number
  ingestedAt: string // ISO date
}

/** One structural unit of a document tree (Document > Section > Clause). */
export interface Clause {
  id: string // e.g. "4.2(b)" or "§ 3" or "¶ 12"
  heading: string
  text: string
}

export interface Section {
  id: string
  heading: string
  clauses: Clause[]
}

export interface DocumentDetail extends DocumentSummary {
  sections: Section[]
}

/** A retrievable unit produced by the chunker; what citations point at. */
export interface Chunk {
  id: string
  documentId: string
  sectionId: string
  clauseId: string
  heading: string
  text: string
}

export interface Citation {
  chunkId: string
  label: string // e.g. "§4.2(b)"
  valid: boolean
}

export type SummarizationStrategy = "naive" | "map_reduce" | "refine"

export interface SummaryResponse {
  documentId: string
  query: string
  answer: string // markdown; inline citations appear as [label] tokens
  citations: Citation[]
  strategy: SummarizationStrategy
  latencyMs: number
}

export interface RetrievalScore {
  chunkId: string
  vectorScore: number // 0-1
  bm25Score: number // 0-1
  rerankScore: number | null // 0-1, null before Phase 4's reranker exists
  fusedRank: number
}

export interface RetrievalResult {
  documentId: string
  query: string
  chunks: Chunk[]
  scores: RetrievalScore[]
}

export type EvalStage = "naive" | "hybrid" | "hybrid_rerank"

export interface EvalMetric {
  stage: EvalStage
  precisionAtK: number
  recallAtK: number
  mrr: number
  citationAccuracy: number
}

export interface EvalRun {
  id: string
  runAt: string
  k: number
  goldenSetSize: number
  metrics: EvalMetric[]
}

export type ChunkingMode = "fixed" | "structural"
export type RetrievalMode = "vector" | "hybrid" | "hybrid_rerank"

export interface PipelineConfig {
  id: string
  label: string
  chunking: ChunkingMode
  retrieval: RetrievalMode
  summarization: SummarizationStrategy
}

export interface CompareResult {
  config: PipelineConfig
  answer: string
  citations: Citation[]
  latencyMs: number
}
