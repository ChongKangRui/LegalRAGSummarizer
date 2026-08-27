import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import type { EvalStage } from "@/lib/types"

const STAGE_LABEL: Record<EvalStage, string> = {
  naive: "Naive",
  hybrid: "+ Hybrid",
  hybrid_rerank: "+ Rerank",
}

const STAGE_COLOR: Record<EvalStage, string> = {
  naive: "bg-stage-naive",
  hybrid: "bg-stage-hybrid",
  hybrid_rerank: "bg-stage-rerank",
}

const STAGE_ORDER: EvalStage[] = ["naive", "hybrid", "hybrid_rerank"]

interface StageBarChartProps {
  title: string
  /** Value per stage, 0-1. Rendered in fixed naive -> hybrid -> hybrid_rerank order. */
  values: Record<EvalStage, number>
}

/**
 * One metric's progression across pipeline stages (naive -> hybrid ->
 * hybrid+rerank) — a single-hue sequential ramp, since the three bars are an
 * ordered progression, not distinct identities (Phase 4's eval harness).
 */
export function StageBarChart({ title, values }: StageBarChartProps) {
  const max = Math.max(...STAGE_ORDER.map((s) => values[s]), 0.01)

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2.5">
        {STAGE_ORDER.map((stage) => (
          <div key={stage} className="flex items-center gap-3">
            <span className="w-20 shrink-0 text-xs text-muted-foreground">{STAGE_LABEL[stage]}</span>
            <div className="h-3.5 flex-1 overflow-hidden rounded-sm bg-muted">
              <div
                className={cn("h-full rounded-r-[4px]", STAGE_COLOR[stage])}
                style={{ width: `${(values[stage] / max) * 100}%` }}
              />
            </div>
            <span className="w-11 shrink-0 text-right font-mono text-xs tabular-nums">
              {(values[stage] * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
