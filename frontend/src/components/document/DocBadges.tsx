import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import type { DocumentStatus, DocumentType } from "@/lib/types"

const TYPE_LABEL: Record<DocumentType, string> = {
  statute: "Statute",
  case_law: "Case law",
  tos: "Terms of Service",
  contract: "Contract",
  agreement : "Agreement"
}

export function DocTypeBadge({ type, className }: { type: DocumentType; className?: string }) {
  return (
    <Badge variant="secondary" className={cn("font-normal", className)}>
      {TYPE_LABEL[type]}
    </Badge>
  )
}

const STATUS_DOT: Record<DocumentStatus, string> = {
  ready: "bg-score-rerank",
  processing: "bg-stage-hybrid",
  error: "bg-destructive",
}

const STATUS_LABEL: Record<DocumentStatus, string> = {
  ready: "Ready",
  processing: "Processing",
  error: "Error",
}

export function DocStatusBadge({ status, className }: { status: DocumentStatus; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-xs text-muted-foreground", className)}>
      <span className={cn("size-1.5 rounded-full", STATUS_DOT[status])} />
      {STATUS_LABEL[status]}
    </span>
  )
}
