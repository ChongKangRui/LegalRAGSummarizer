import { lazy, Suspense } from "react"
import { Route, Routes } from "react-router-dom"
import { AppShell } from "@/components/layout/AppShell"
import { Skeleton } from "@/components/ui/skeleton"

const LibraryPage = lazy(() => import("@/pages/LibraryPage"))
const DocumentPage = lazy(() => import("@/pages/DocumentPage"))
const InspectorPage = lazy(() => import("@/pages/InspectorPage"))
const EvalDashboardPage = lazy(() => import("@/pages/EvalDashboardPage"))
const ComparePage = lazy(() => import("@/pages/ComparePage"))
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"))

function PageFallback() {
  return (
    <div className="mx-auto w-full max-w-5xl space-y-4">
      <Skeleton className="h-8 w-1/3" />
      <Skeleton className="h-64 w-full" />
    </div>
  )
}

export default function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<LibraryPage />} />
          <Route path="documents/:documentId" element={<DocumentPage />} />
          <Route path="documents/:documentId/inspector" element={<InspectorPage />} />
          <Route path="documents/:documentId/compare" element={<ComparePage />} />
          <Route path="eval" element={<EvalDashboardPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
