import { Link } from "react-router-dom"
import { FileWarning, Layers } from "lucide-react"
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { DocStatusBadge, DocTypeBadge } from "@/components/document/DocBadges"
import { useDocuments } from "@/hooks/queries"

export default function LibraryPage() {
  const { data: documents, isLoading, isError } = useDocuments()
  console.log(documents);
  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Library</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Curated sample documents — statutes, case law, ToS, and EDGAR contracts. Ask a question or
          request a summary on any of them.
        </p>
      </div>

      {isError && (
        <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          <FileWarning className="size-4 shrink-0" />
          Couldn't load the document registry. Is the backend running?
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading &&
          Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="mt-2 h-3 w-1/2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-3 w-full" />
              </CardContent>
            </Card>
          ))}

        {documents?.map((doc) => (
          <Link key={doc.id} to={`/documents/${doc.id}`} className="group">
            <Card className="h-full transition-colors group-hover:border-primary/40">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <DocTypeBadge type={doc.type} />
                  <DocStatusBadge status={doc.status} />
                </div>
                <CardTitle className="mt-2 text-base leading-snug">{doc.title}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">{doc.source}</CardContent>
              <CardFooter className="flex items-center justify-between text-xs text-muted-foreground">
                <span className="inline-flex items-center gap-1.5">
                  <Layers className="size-3.5" />
                  {doc.chunkCount} chunks
                  
                </span>
                <span>{doc.ingestedAt}</span>
              </CardFooter>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
