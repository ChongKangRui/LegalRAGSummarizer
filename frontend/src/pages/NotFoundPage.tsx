import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"

export default function NotFoundPage() {
  return (
    <div className="mx-auto flex w-full max-w-md flex-1 flex-col items-center justify-center gap-3 text-center">
      <h1 className="text-2xl font-semibold tracking-tight">Page not found</h1>
      <p className="text-sm text-muted-foreground">
        That page doesn't exist, or the document it needs was moved.
      </p>
      <Button asChild variant="outline" className="mt-2">
        <Link to="/">Back to Library</Link>
      </Button>
    </div>
  )
}
