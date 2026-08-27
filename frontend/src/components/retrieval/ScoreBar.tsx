import { cn } from "@/lib/utils"

interface ScoreBarProps {
  /** 0-1. */
  value: number | null
  colorClassName: string
  className?: string
}

/** One thin, directly-labeled score bar — used for vector/BM25/rerank scores. */
export function ScoreBar({ value, colorClassName, className }: ScoreBarProps) {
  if (value === null) {
    return <span className={cn("font-mono text-xs text-muted-foreground", className)}>—</span>
  }
  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      <div className="h-1.5 w-16 shrink-0 overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full rounded-full", colorClassName)}
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="w-9 shrink-0 font-mono text-xs tabular-nums text-muted-foreground">
        {value.toFixed(2)}
      </span>
    </div>
  )
}

const LEGEND_ITEMS = [
  { label: "Vector", colorClassName: "bg-score-vector" },
  { label: "BM25", colorClassName: "bg-score-bm25" },
  { label: "Rerank", colorClassName: "bg-score-rerank" },
] as const

/** Legend for the three score-bar colors — always present alongside them (2+ series). */
export function ScoreLegend({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-4 text-xs text-muted-foreground", className)}>
      {LEGEND_ITEMS.map((item) => (
        <span key={item.label} className="inline-flex items-center gap-1.5">
          <span className={cn("size-2 rounded-full", item.colorClassName)} />
          {item.label}
        </span>
      ))}
    </div>
  )
}
