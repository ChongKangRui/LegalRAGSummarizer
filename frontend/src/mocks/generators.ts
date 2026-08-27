import type {
  Chunk,
  Citation,
  CompareResult,
  DocumentType,
  EvalRun,
  PipelineConfig,
  RetrievalResult,
  RetrievalScore,
  SummarizationStrategy,
  SummaryResponse,
} from "@/lib/types"
import { getChunksForDocument, getDocumentById } from "@/mocks/documents"

/**
 * Deterministic "fake pipeline" used until the real backend exists.
 *
 * Everything here is seeded from (documentId, query) so the same question
 * against the same document always returns the same mock result — good
 * enough to demo retrieval scores, citations, and the eval/compare pages
 * without a live index. Swap the call sites in `lib/api.ts`, not this file,
 * once the real endpoints exist.
 */

function hashString(input: string): number {
  let hash = 2166136261
  for (let i = 0; i < input.length; i++) {
    hash ^= input.charCodeAt(i)
    hash = Math.imul(hash, 16777619)
  }
  return hash >>> 0
}

function mulberry32(seed: number) {
  let a = seed
  return () => {
    a |= 0
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function shuffle<T>(items: T[], rng: () => number): T[] {
  const copy = [...items]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}

/** How a raw clause id renders as an inline citation, per doc type convention. */
export function formatCitationLabel(type: DocumentType, clauseId: string): string {
  if (clauseId.startsWith("§") || clauseId.startsWith("¶")) return clauseId
  if (type === "case_law") return `¶${clauseId}`
  return `§${clauseId}`
}

export function scoreChunks(documentId: string, query: string): RetrievalScore[] {
  const chunks = getChunksForDocument(documentId)
  const rng = mulberry32(hashString(`${documentId}::${query}`))
  const shuffled = shuffle(chunks, rng)
  const selected = shuffled.slice(0, Math.min(6, shuffled.length))

  const withVectorAndBm25 = selected.map((chunk) => ({
    chunk,
    vectorScore: 0.55 + rng() * 0.43,
    bm25Score: 0.35 + rng() * 0.6,
  }))

  // Reciprocal Rank Fusion of the two signals, then a rerank pass that
  // perturbs the fused order slightly (a cross-encoder rarely agrees with
  // RRF exactly) — mirrors the naive -> hybrid -> hybrid+rerank progression.
  const byVector = [...withVectorAndBm25].sort((a, b) => b.vectorScore - a.vectorScore)
  const byBm25 = [...withVectorAndBm25].sort((a, b) => b.bm25Score - a.bm25Score)
  const rrf = new Map<string, number>()
  const k = 60
  byVector.forEach((entry, rank) => {
    rrf.set(entry.chunk.id, (rrf.get(entry.chunk.id) ?? 0) + 1 / (k + rank + 1))
  })
  byBm25.forEach((entry, rank) => {
    rrf.set(entry.chunk.id, (rrf.get(entry.chunk.id) ?? 0) + 1 / (k + rank + 1))
  })

  const fusedOrder = [...withVectorAndBm25].sort(
    (a, b) => (rrf.get(b.chunk.id) ?? 0) - (rrf.get(a.chunk.id) ?? 0),
  )

  const reranked = shuffle(fusedOrder, rng)
    .map((entry) => ({ ...entry, rerankScore: 0.5 + rng() * 0.49 }))
    .sort((a, b) => b.rerankScore - a.rerankScore)

  return reranked.map((entry, index) => ({
    chunkId: entry.chunk.id,
    vectorScore: Number(entry.vectorScore.toFixed(3)),
    bm25Score: Number(entry.bm25Score.toFixed(3)),
    rerankScore: Number(entry.rerankScore.toFixed(3)),
    fusedRank: index + 1,
  }))
}

export function retrieve(documentId: string, query: string): RetrievalResult {
  const scores = scoreChunks(documentId, query)
  const chunks = getChunksForDocument(documentId)
  const byId = new Map(chunks.map((c) => [c.id, c] as const))
  return {
    documentId,
    query,
    chunks: scores.map((s) => byId.get(s.chunkId)).filter((c): c is Chunk => Boolean(c)),
    scores,
  }
}

const STRATEGY_LATENCY_MS: Record<SummarizationStrategy, [number, number]> = {
  naive: [400, 1200],
  map_reduce: [2200, 4800],
  refine: [3000, 6500],
}

function randomInRange(rng: () => number, [min, max]: [number, number]): number {
  return Math.round(min + rng() * (max - min))
}

export function summarize(
  documentId: string,
  query: string,
  strategy: SummarizationStrategy = "naive",
): SummaryResponse {
  const doc = getDocumentById(documentId)
  const result = retrieve(documentId, query)
  const rng = mulberry32(hashString(`${documentId}::${query}::${strategy}`))
  const top = result.chunks.slice(0, 3)

  if (!doc || top.length === 0) {
    return {
      documentId,
      query,
      answer: "No relevant clauses were retrieved for this question.",
      citations: [],
      strategy,
      latencyMs: randomInRange(rng, STRATEGY_LATENCY_MS[strategy]),
    }
  }

  const retrievedIds = new Set(result.chunks.map((c) => c.id))
  const sentences = top.map((chunk) => {
    const label = formatCitationLabel(doc.type, chunk.clauseId)
    const firstSentence = chunk.text.split(". ")[0]
    return `${firstSentence.replace(/\.$/, "")} [${label}].`
  })

  // Deterministically inject one fabricated citation ~1 in 3 queries, so the
  // Document view's citation validator has something real to catch.
  const injectBadCitation = rng() < 0.33
  const otherDocChunks = getChunksForDocument(documentId).filter((c) => !retrievedIds.has(c.id))
  if (injectBadCitation && otherDocChunks.length > 0) {
    const fabricated = otherDocChunks[Math.floor(rng() * otherDocChunks.length)]
    const label = formatCitationLabel(doc.type, fabricated.clauseId)
    sentences.push(`This also affects related obligations elsewhere in the agreement [${label}].`)
  }

  const citations: Citation[] = sentences.flatMap((sentence) => {
    const matches = [...sentence.matchAll(/\[([^\]]+)\]/g)]
    return matches.map((m) => {
      const label = m[1]
      const chunk = top.find((c) => formatCitationLabel(doc.type, c.clauseId) === label)
      const fabricatedMatch = otherDocChunks.find(
        (c) => formatCitationLabel(doc.type, c.clauseId) === label,
      )
      const chunkId = chunk?.id ?? fabricatedMatch?.id ?? ""
      return { chunkId, label, valid: retrievedIds.has(chunkId) }
    })
  })

  const strategyPrefix =
    strategy === "naive"
      ? ""
      : strategy === "map_reduce"
        ? "Summarizing each section, then combining: "
        : "Running refine pass across sections: "

  return {
    documentId,
    query,
    answer: strategyPrefix + sentences.join(" "),
    citations,
    strategy,
    latencyMs: randomInRange(rng, STRATEGY_LATENCY_MS[strategy]),
  }
}

export function generateEvalRun(): EvalRun {
  return {
    id: "eval-run-2026-08-24",
    runAt: "2026-08-24T09:15:00Z",
    k: 5,
    goldenSetSize: 42,
    metrics: [
      { stage: "naive", precisionAtK: 0.41, recallAtK: 0.38, mrr: 0.34, citationAccuracy: 0.52 },
      { stage: "hybrid", precisionAtK: 0.63, recallAtK: 0.6, mrr: 0.58, citationAccuracy: 0.74 },
      {
        stage: "hybrid_rerank",
        precisionAtK: 0.79,
        recallAtK: 0.72,
        mrr: 0.75,
        citationAccuracy: 0.88,
      },
    ],
  }
}

export const pipelinePresets: PipelineConfig[] = [
  {
    id: "cfg-naive",
    label: "Naive baseline",
    chunking: "fixed",
    retrieval: "vector",
    summarization: "naive",
  },
  {
    id: "cfg-hybrid",
    label: "Structural + hybrid",
    chunking: "structural",
    retrieval: "hybrid",
    summarization: "naive",
  },
  {
    id: "cfg-full",
    label: "Structural + hybrid + rerank",
    chunking: "structural",
    retrieval: "hybrid_rerank",
    summarization: "refine",
  },
]

export function compareConfigs(
  documentId: string,
  query: string,
  configs: PipelineConfig[],
): CompareResult[] {
  return configs.map((config) => {
    const response = summarize(documentId, query, config.summarization)
    // The naive config is deliberately worse: fewer citations, shorter answer,
    // to make the side-by-side actually show something.
    const degraded = config.chunking === "fixed" && config.retrieval === "vector"
    return {
      config,
      answer: degraded ? response.answer.split(" ").slice(0, 24).join(" ") + "…" : response.answer,
      citations: degraded ? response.citations.slice(0, 1) : response.citations,
      latencyMs: degraded ? Math.round(response.latencyMs * 0.5) : response.latencyMs,
    }
  })
}
