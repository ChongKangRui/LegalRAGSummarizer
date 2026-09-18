import { useMutation, useQuery } from "@tanstack/react-query"
import { compareApi, documentsApi, evalApi, queryApi } from "@/lib/api"
import type {  SummarizationStrategy } from "@/lib/types"

export function useDocuments() {
  return useQuery({
    queryKey: ["documents"],
    queryFn: documentsApi.list,
  })
}

export function useDocument(documentId: string | undefined) {
  return useQuery({
    queryKey: ["documents", documentId],
    queryFn: () => documentsApi.get(documentId as string),
    enabled: Boolean(documentId),
  })
}

export function useSummarize() {
  return useMutation({
    mutationFn: ({
      documentId,
      query,
      strategy,
    }: {
      documentId: string
      query: string
      strategy?: SummarizationStrategy
    }) => queryApi.summarize(documentId, query, strategy),
  })
}

export function useStrategies() {
  return useQuery({
    queryKey: ["strategies"],
    queryFn: queryApi.getStrategies,
    staleTime: Infinity,
  })
}

export function useRetrieve() {
  return useMutation({
    mutationFn: ({ documentId, query }: { documentId: string; query: string }) =>
      queryApi.retrieve(documentId, query),
  })
}

export function useEvalRun() {
  return useQuery({
    queryKey: ["eval", "latest"],
    queryFn: evalApi.getLatestRun,
  })
}



export function useCompare() {
  return useMutation({
    mutationFn: ({
      documentId,
      query,
      strategies,
    }: {
      documentId: string
      query: string
      strategies: string[]
    }) => compareApi.run(documentId, query, strategies),
  })
}
