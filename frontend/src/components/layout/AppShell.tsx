import { Link, Outlet, useLocation, useParams } from "react-router-dom"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Separator } from "@/components/ui/separator"
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/layout/AppSidebar"
import { useDocument } from "@/hooks/queries"

const PAGE_LABELS: Record<string, string> = {
  inspector: "Inspector",
  compare: "Compare",
}

function HeaderBreadcrumb() {
  
  const { documentId } = useParams<{ documentId?: string }>()
  const { data: doc } = useDocument(documentId)
  const location = useLocation()
  const page = documentId
    ? location.pathname.split(`/documents/${documentId}`)[1]?.replace(/^\//, "") || undefined
    : undefined

    console.log("Link=", location.pathname.split(`/documents/${documentId}`));

  if (!documentId) {
    return (
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbPage>Library</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
    )
  }

  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink asChild>
            <Link to="/">Library</Link>
          </BreadcrumbLink>
        </BreadcrumbItem>
        <BreadcrumbSeparator />
        <BreadcrumbItem>
          {page ? (
            <BreadcrumbLink asChild>
              <Link to={`/documents/${documentId}`} className="max-w-64 truncate">
                {doc?.title ?? "Document"}
              </Link>
            </BreadcrumbLink>
          ) : (
            <BreadcrumbPage className="max-w-64 truncate">{doc?.title ?? "Document"}</BreadcrumbPage>
          )}
        </BreadcrumbItem>
        {page ? (
          <>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>{PAGE_LABELS[page] ?? page}</BreadcrumbPage>
            </BreadcrumbItem>
          </>
        ) : null}
      </BreadcrumbList>
    </Breadcrumb>
  )
}

export function AppShell() {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="flex h-14 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-2 h-4" />
          <HeaderBreadcrumb />
        </header>
        <div className="flex flex-1 flex-col overflow-y-auto p-6">
          <Outlet />
        </div>
      </SidebarInset>
    </SidebarProvider>
  )
}
