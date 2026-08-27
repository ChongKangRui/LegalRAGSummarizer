import { useState } from "react"
import { useParams } from "react-router-dom"
import { GitCompareArrows, Loader2, TriangleAlert } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { CitationText } from "@/components/citation/CitationText"
import { DocTypeBadge } from "@/components/document/DocBadges"
import { useCompare, useDocument, usePipelinePresets } from "@/hooks/queries"
import type { PipelineConfig } from "@/lib/types"

export default function ComparePage() {
  const { documentId } = useParams<{ documentId: string }>()
  const { data: doc } = useDocument(documentId)
  const { data: presets, isLoading: presetsLoading } = usePipelinePresets()
  const compare = useCompare()

  const [query, setQuery] = useState("")
  const [leftId, setLeftId] = useState<string>("")
  const [rightId, setRightId] = useState<string>("")

  // Default to "naive baseline" vs. "full pipeline" once presets load, without
  // syncing state from props in an effect — derive it, only falling back to
  // local state once the user actually picks something else.
  const effectiveLeftId = leftId || presets?.[0]?.id || ""
  const effectiveRightId = rightId || presets?.[presets.length - 1]?.id || ""

  function handleRun() {
    if (!documentId || !query.trim() || !presets) return
    const left = presets.find((p) => p.id === effectiveLeftId)
    const right = presets.find((p) => p.id === effectiveRightId)
    if (!left || !right) return
    compare.mutate({ documentId, query: query.trim(), configs: [left, right] })
  }

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight">
          <GitCompareArrows className="size-6" />
          Compare
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Same question, two pipeline configs, side by side — e.g. naive baseline vs. structural
          chunking + hybrid retrieval + rerank.
        </p>
      </div>

      {doc && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <DocTypeBadge type={doc.type} />
          {doc.title}
        </div>
      )}

      <Card>
        <CardContent className="flex flex-col gap-3 pt-6">
          <Input
            placeholder="e.g. What happens if payment is late?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleRun()}
          />
          <div className="flex flex-wrap items-center gap-2">
            <ConfigSelect
              label="Config A"
              presets={presets}
              value={effectiveLeftId}
              onChange={setLeftId}
              loading={presetsLoading}
            />
            <span className="text-xs text-muted-foreground">vs.</span>
            <ConfigSelect
              label="Config B"
              presets={presets}
              value={effectiveRightId}
              onChange={setRightId}
              loading={presetsLoading}
            />
            <Button onClick={handleRun} disabled={!query.trim() || compare.isPending} className="ml-auto">
              {compare.isPending ? <Loader2 className="size-4 animate-spin" /> : null}
              Run comparison
            </Button>
          </div>
        </CardContent>
      </Card>

      {compare.isError && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <TriangleAlert className="size-4 shrink-0" />
          Comparison failed. Is the backend running?
        </div>
      )}

      {compare.isPending && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Skeleton className="h-56 w-full" />
          <Skeleton className="h-56 w-full" />
        </div>
      )}

      {compare.data && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {compare.data.map((result) => (
            <Card key={result.config.id}>
              <CardHeader>
                <CardTitle className="text-base">{result.config.label}</CardTitle>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  <Badge variant="outline" className="font-mono text-xs font-normal">
                    chunking: {result.config.chunking}
                  </Badge>
                  <Badge variant="outline" className="font-mono text-xs font-normal">
                    retrieval: {result.config.retrieval}
                  </Badge>
                  <Badge variant="outline" className="font-mono text-xs font-normal">
                    summarize: {result.config.summarization}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <CitationText text={result.answer} citations={result.citations} className="text-sm" />
                <p className="text-xs text-muted-foreground">
                  {result.citations.length} citation{result.citations.length === 1 ? "" : "s"} ·{" "}
                  {result.latencyMs}ms
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

function ConfigSelect({
  label,
  presets,
  value,
  onChange,
  loading,
}: {
  label: string
  presets: PipelineConfig[] | undefined
  value: string
  onChange: (id: string) => void
  loading: boolean
}) {
  return (
    <Select value={value} onValueChange={onChange} disabled={loading || !presets}>
      <SelectTrigger className="w-56">
        <SelectValue placeholder={label} />
      </SelectTrigger>
      <SelectContent>
        {presets?.map((p) => (
          <SelectItem key={p.id} value={p.id}>
            {p.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
