import { useState } from "react"
import { useParams } from "react-router-dom"
import { Download, Loader2, Sparkles, TriangleAlert } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { Textarea } from "@/components/ui/textarea"
import { DocStatusBadge, DocTypeBadge } from "@/components/document/DocBadges"
import { CitationText } from "@/components/citation/CitationText"
import { useDocument, useSummarize } from "@/hooks/queries"
import {queryApi} from "@/lib/api"
import { downloadTextFile } from "@/lib/download"
import { cn } from "@/lib/utils"
import type { Citation, SummarizationStrategy } from "@/lib/types"

const STRATEGY_OPTIONS: { value: SummarizationStrategy; label: string }[] = [
  { value: "naive", label: "Naive (truncate + stuff)" },
  { value: "map_reduce", label: "Map-reduce" },
  { value: "refine", label: "Refine" },
]

export default function DocumentPage() {
  const { documentId } = useParams<{ documentId: string }>()
  const { data: doc, isLoading } = useDocument(documentId)
  const summarize = useSummarize()

  const [query, setQuery] = useState("")
  const [strategy, setStrategy] = useState<SummarizationStrategy>("naive")
  const [activeClauseId, setActiveClauseId] = useState<string | null>(null)

  const [answer, setAnswer] = useState("")
  const [citations, setCitations] = useState<Citation[]>()
  const [latency, setLatency] = useState(0)
  const [actualStrategy, setActualStrategy] = useState<SummarizationStrategy>("naive")

  const [streaming, setStreaming] = useState(false)
  const [streamError, setStreamError] = useState(false)
  const [askedQuery, setAskedQuery] = useState("")

  // Non-streaming path — kept for reference, not wired to the button.
  function handleAsk() {
    if (!documentId || !query.trim()) return
    summarize.mutate(
      { documentId, query: query.trim(), strategy },
      {
        onSuccess: (data) => {
          setCitations(data.citations)
          setLatency(data.latencyMs)
          setActualStrategy(data.strategy)
        },
      },
    )
  }

  async function handleAskStreaming() {
    if (!documentId || !query.trim() || streaming) return

    const asked = query.trim()
    setAskedQuery(asked)
    setAnswer("")
    setCitations(undefined)
    setLatency(0)
    setStreamError(false)
    setStreaming(true)

    try {
      await queryApi.summarizeWithStream(
        documentId,
        asked,
        strategy,
        setAnswer,
        setCitations,
        setLatency,
        setActualStrategy,
      )
    } catch {
      setStreamError(true)
    } finally {
      setStreaming(false)
    }
  }

  function handleCiteClick(citation: Citation) {
    // chunkId looks like "tos-atlassian::chunk-14.2::0" — the middle segment is the clause
    const clauseId = citation.chunkId.split("::")[1]?.replace(/^chunk-/, "") ?? ""
    setActiveClauseId(clauseId)
    const el = document.getElementById(`clause-${clauseId}`)
    el?.scrollIntoView({ behavior: "smooth", block: "center" })
  }

  function handleExport() {
    if (!doc || !answer) return
    const lines = [
      `# ${doc.title}`,
      "",
      `**Question:** ${askedQuery}`,
      "",
      answer,
      "",
      "## Citations",
      ...(citations ?? []).map(
        (c) => `- \`${c.label}\`${c.valid ? "" : " — ⚠️ could not be validated against a retrieved chunk"}`,
      ),
    ]
    downloadTextFile(`${doc.id}-summary.md`, lines.join("\n"))
  }

  if (isLoading || !doc) {
    return (
      <div className="mx-auto w-full max-w-6xl space-y-4">
        <Skeleton className="h-8 w-1/2" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }


  return (
    <div className="mx-auto grid w-full max-w-6xl flex-1 grid-cols-1 gap-6 lg:grid-cols-[1fr_400px]">
      {/* Source */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="mb-2 flex items-center gap-2">
                <DocTypeBadge type={doc.type} />
                <DocStatusBadge status={doc.status} />
              </div>
              <CardTitle className="text-lg leading-snug">{doc.title}</CardTitle>
            </div>
          </div>
        </CardHeader>
        <CardContent className="min-h-0 flex-1 p-0 ">
          
          <ScrollArea className="h-[calc(100vh-14rem)] px-6 pb-6">
            <div className="space-y-6">
              {doc.sections.map((section) => (
                <div key={section.id} className="">
                  <h3 className="text-sm font-semibold text-foreground">{section.heading}</h3>
                  <div className="mt-2 space-y-3 border-l pl-4 lg:max-w-[100%]">
                    {section.clauses.map((clause,i) => (
                      <div
                        key={`${section.id}-${clause.id}-${i}`}
                        id={`clause-${clause.id}`}
                        className={cn(
                          "scroll-mt-4 rounded-md border border-transparent px-2 py-1.5 text-sm text-muted-foreground break-words transition-colors ",
                          activeClauseId === clause.id &&
                            "border-primary/30 bg-primary/5 text-foreground",
                        )}
                      >
                        <span className="mr-1.5 font-mono text-xs font-medium text-foreground">
                          {clause.id}
                        </span>
                        {clause.heading !== clause.id && (
                          <span className="mr-1.5 font-medium text-foreground">{clause.heading}.</span>
                        )}
                        {clause.text}
                      </div>
                    ))}
                  </div> 
                
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Ask / Summarize */}
      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Ask</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Textarea
              placeholder="e.g. What happens if payment is late?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              rows={3}
            />
            <div className="flex items-center gap-2">
              <Select value={strategy} onValueChange={(v) => setStrategy(v as SummarizationStrategy)}>
                <SelectTrigger className="flex-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STRATEGY_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button onClick={handleAskStreaming} disabled={!query.trim() || streaming}>
                {streaming ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <Sparkles className="size-4" />
                )}
                Ask
              </Button>
            </div>
          </CardContent>
        </Card>

        {streaming && !answer && (
          <Card>
            <CardContent className="space-y-2 pt-6">
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-5/6" />
              <Skeleton className="h-3 w-2/3" />
            </CardContent>
          </Card>
        )}

        {streamError && (
          <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            <TriangleAlert className="size-4 shrink-0" />
            Couldn't get an answer. Is the backend running?
          </div>
        )}

        {answer && (
          <Card className="flex-1">
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle className="text-base">Answer</CardTitle>
              <Button variant="ghost" size="sm" onClick={handleExport}>
                <Download className="size-3.5" />
                Export .md
              </Button>
            </CardHeader>
            <CardContent className="space-y-4">
              <CitationText
                text={answer}
                // citations={summarize.data.citations}
                citations={citations ?? []}
                onCiteClick={handleCiteClick}
                className="text-sm"
              />
              <Separator />
              <div className="space-y-1.5">
                <p className="text-xs font-medium text-muted-foreground">
                  Citations ({citations?.length ?? 0})
                </p>
                <ul className="space-y-1 text-xs">
                   {citations?.map((c, i) => (
                    <li
                      key={i}
                      className={cn(
                        "flex items-center gap-1.5",
                        c.valid ? "text-muted-foreground" : "text-destructive",
                      )}
                    >
                      {!c.valid && <TriangleAlert className="size-3 shrink-0" />}
                      <code className="font-mono">{c.label}</code>
                      {!c.valid && <span>— not in retrieved chunks</span>}
                    </li>
                  ))} 
                </ul>
              </div>
              <p className="text-xs text-muted-foreground">
                 {actualStrategy} · {latency.toFixed(2)}ms 
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
