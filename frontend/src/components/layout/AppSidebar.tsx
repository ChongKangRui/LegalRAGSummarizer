import { NavLink, useParams } from "react-router-dom"
import {
  BookMarked,
  FileText,
  GitCompareArrows,
  Gauge,
  Scale,
  Telescope,
} from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

interface NavItem {
  to: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  /** true if this page needs a document selected to be useful */
  needsDocument?: boolean
}

const navItems: NavItem[] = [
  { to: "/", label: "Library", icon: BookMarked },
  { to: "/documents/:id", label: "Document", icon: FileText, needsDocument: true },
  { to: "/documents/:id/inspector", label: "Inspector", icon: Telescope, needsDocument: true },
  { to: "/eval", label: "Eval dashboard", icon: Gauge },
  { to: "/documents/:id/compare", label: "Compare", icon: GitCompareArrows, needsDocument: true },
]

export function AppSidebar() {
  const { documentId } = useParams<{ documentId: string }>()

  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <div className="flex items-center gap-2 px-2 py-1.5">
          <Scale className="size-5 shrink-0 text-sidebar-primary" />
          <div className="flex flex-col leading-tight group-data-[collapsible=icon]:hidden">
            <span className="text-sm font-semibold">Legal RAG</span>
            <span className="text-xs text-muted-foreground">Summarizer</span>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Workspace</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => {
                const resolvedTo = item.needsDocument
                  ? item.to.replace(":id", documentId ?? "")
                  : item.to
                const disabled = item.needsDocument && !documentId
                return (
                  <SidebarMenuItem key={item.to}>
                    <SidebarMenuButton asChild disabled={disabled} tooltip={item.label}>
                      {disabled ? (
                        <span className="opacity-50">
                          <item.icon />
                          <span>{item.label}</span>
                        </span>
                      ) : (
                        <NavLink
                          to={resolvedTo}
                          end={item.to === "/"}
                          className={({ isActive }) =>
                            isActive ? "font-medium text-sidebar-accent-foreground" : undefined
                          }
                        >
                          <item.icon />
                          <span>{item.label}</span>
                        </NavLink>
                      )}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
