import { TriangleAlert } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Citation } from "@/lib/types"

interface CitationTextProps {
  text: string
  citations: Citation[]
  onCiteClick?: (citation: Citation) => void
  className?: string
}

/**
 * Renders model output that contains inline `[§4.2(b)]`-style citation
 * tokens, turning each token into a clickable badge. A citation whose
 * `valid` flag is false (didn't map to an actually-retrieved chunk — see
 * Phase 3's citation validator) renders as a flagged, distinct badge instead
 * of failing silently.
 */
export function CitationText({ text, citations, onCiteClick, className }: CitationTextProps) {
  
  const parts = text.split(/(\[[^\]]+\])/g)
 
  return (
    <p className={cn("leading-relaxed", className)}>
      {parts.map((part, i) => {
        const match = part.match(/^\[([^\]]+)\]$/)
        if (!match) return <span key={i}>{part}</span>

        const label = match[1]
        //const idx = citations.findIndex((c) => c.label === label)
        const citation = citations.find((c) => c.label === label)
        const invalid = citation?.valid === false
        
        return (
          <button
            key={i}
            type="button"
            disabled={!citation}
            onClick={() => citation && onCiteClick?.(citation)}
            className={cn(
              "mx-0.5 inline-flex items-center gap-0.5 rounded px-1 align-baseline font-mono text-xs font-medium ring-1 ring-inset transition-colors",
              invalid
                ? "bg-destructive/10 text-destructive ring-destructive/30 hover:bg-destructive/20"
                : "bg-primary/10 text-primary ring-primary/20 hover:bg-primary/20",
              !citation && "cursor-default opacity-60",
            )}
            title={invalid ? "Citation does not map to a retrieved chunk" : undefined}
          >
            {label}
            {invalid && <TriangleAlert className="size-3" />}
            
          </button>
        )
      })}
    </p>
  )
}
