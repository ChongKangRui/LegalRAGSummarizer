import { Gauge, TriangleAlert } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { StageBarChart } from "@/components/eval/StageBarChart"
import { useEvalRun } from "@/hooks/queries"
import type { EvalStage } from "@/lib/types"

const STAGE_LABEL: Record<EvalStage, string> = {
  naive: "Naive (vector only)",
  hybrid: "+ Hybrid (vector + BM25)",
  hybrid_rerank: "+ Rerank (cross-encoder)",
}

export default function EvalDashboardPage() {
  const { data: run, isLoading, isError } = useEvalRun()

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
          <Gauge className="size-6" />
          Eval dashboard
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Retrieval quality against the golden set, at each stage of the pipeline — so improvements
          are numbers, not vibes.
        </p>
      </div>

      {isError && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <TriangleAlert className="size-4 shrink-0" />
          Couldn't load the latest eval run. Is the backend running?
        </div>
      )}

      {isLoading && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-40 w-full" />
          ))}
        </div>
      )}

      {run && (
        <>
          <p className="text-sm text-muted-foreground">
            {run.goldenSetSize} labeled questions · k = {run.k} · last run{" "}
            {new Date(run.runAt).toLocaleString()}
          </p>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <StageBarChart
              title={`Precision@${run.k}`}
              values={Object.fromEntries(run.metrics.map((m) => [m.stage, m.precisionAtK])) as Record<
                EvalStage,
                number
              >}
            />
            <StageBarChart
              title={`Recall@${run.k}`}
              values={Object.fromEntries(run.metrics.map((m) => [m.stage, m.recallAtK])) as Record<
                EvalStage,
                number
              >}
            />
            <StageBarChart
              title="MRR"
              values={Object.fromEntries(run.metrics.map((m) => [m.stage, m.mrr])) as Record<
                EvalStage,
                number
              >}
            />
            <StageBarChart
              title="Citation accuracy"
              values={Object.fromEntries(
                run.metrics.map((m) => [m.stage, m.citationAccuracy]),
              ) as Record<EvalStage, number>}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Raw metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Stage</TableHead>
                    <TableHead>Precision@{run.k}</TableHead>
                    <TableHead>Recall@{run.k}</TableHead>
                    <TableHead>MRR</TableHead>
                    <TableHead>Citation accuracy</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {run.metrics.map((m) => (
                    <TableRow key={m.stage}>
                      <TableCell className="font-medium">{STAGE_LABEL[m.stage]}</TableCell>
                      <TableCell className="font-mono text-sm">{m.precisionAtK.toFixed(2)}</TableCell>
                      <TableCell className="font-mono text-sm">{m.recallAtK.toFixed(2)}</TableCell>
                      <TableCell className="font-mono text-sm">{m.mrr.toFixed(2)}</TableCell>
                      <TableCell className="font-mono text-sm">
                        {m.citationAccuracy.toFixed(2)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
