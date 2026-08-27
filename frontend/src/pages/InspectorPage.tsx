import { useState } from "react"
import { useParams } from "react-router-dom"
import { Loader2, Telescope, TriangleAlert } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { DocTypeBadge } from "@/components/document/DocBadges"
import { ScoreBar, ScoreLegend } from "@/components/retrieval/ScoreBar"
import { useDocument, useRetrieve } from "@/hooks/queries"

export default function InspectorPage() {
  const { documentId } = useParams<{ documentId: string }>()
  const { data: doc, isLoading: docLoading } = useDocument(documentId)
  const retrieve = useRetrieve()

  const [query, setQuery] = useState("")

  function handleRun() {
    if (!documentId || !query.trim()) return
    retrieve.mutate({ documentId, query: query.trim() })
  }

  const data = retrieve.data
  const rows = data?.scores.map((score) => ({
    score,
    chunk: data.chunks.find((c) => c.id === score.chunkId),
  }))

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
          <Telescope className="size-6" />
          Retrieval inspector
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Run a query and see exactly which chunks were retrieved, and how the vector, BM25, and
          rerank scores compare for each.
        </p>
      </div>

      {docLoading ? (
        <Skeleton className="h-6 w-64" />
      ) : (
        doc && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <DocTypeBadge type={doc.type} />
            {doc.title}
          </div>
        )
      )}

      <Card>
        <CardContent className="flex items-center gap-2 pt-6">
          <Input
            placeholder="e.g. When can Northwind suspend access?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleRun()}
          />
          <Button onClick={handleRun} disabled={!query.trim() || retrieve.isPending}>
            {retrieve.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
            Run retrieval
          </Button>
        </CardContent>
      </Card>

      {retrieve.isError && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <TriangleAlert className="size-4 shrink-0" />
          Retrieval failed. Is the backend running?
        </div>
      )}

      {data && rows && (
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-base">
              Results for <span className="font-normal text-muted-foreground">“{data.query}”</span>
            </CardTitle>
            <ScoreLegend />
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">Rank</TableHead>
                  <TableHead className="w-28">Clause</TableHead>
                  <TableHead>Excerpt</TableHead>
                  <TableHead className="w-32">Vector</TableHead>
                  <TableHead className="w-32">BM25</TableHead>
                  <TableHead className="w-32">Rerank</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map(({ score, chunk }) => (
                  <TableRow key={score.chunkId}>
                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {score.fusedRank}
                    </TableCell>
                    <TableCell className="font-mono text-xs font-medium">
                      {chunk?.clauseId}
                    </TableCell>
                    <TableCell className="max-w-xs text-sm text-muted-foreground">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <span className="line-clamp-1 cursor-default">{chunk?.text}</span>
                        </TooltipTrigger>
                        <TooltipContent className="max-w-sm">{chunk?.text}</TooltipContent>
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <ScoreBar value={score.vectorScore} colorClassName="bg-score-vector" />
                    </TableCell>
                    <TableCell>
                      <ScoreBar value={score.bm25Score} colorClassName="bg-score-bm25" />
                    </TableCell>
                    <TableCell>
                      <ScoreBar value={score.rerankScore} colorClassName="bg-score-rerank" />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
