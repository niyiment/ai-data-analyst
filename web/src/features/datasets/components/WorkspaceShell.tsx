"use client";

import {
  BarChart3,
  CheckCircle2,
  Database,
  FileText,
  LayoutDashboard,
  Menu,
  Settings,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { Button } from "@/components/ui/button";
import type { SessionInfo } from "@/features/sessions";
import { cn } from "@/lib/utils";
import { SidebarSessionPanel } from "./SidebarSessionPanel";

export type WorkspacePage =
  "overview" | "analyst" | "datasets" | "reports" | "evaluation" | "settings";

const PAGE_LABELS: Record<WorkspacePage, string> = {
  overview: "Overview",
  analyst: "AI Analyst",
  datasets: "Datasets",
  reports: "Reports",
  evaluation: "Evaluation",
  settings: "Settings",
};

const NAV_ITEMS: {
  id: WorkspacePage;
  label: string;
  icon: typeof LayoutDashboard;
  badge?: string;
}[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "analyst", label: "AI Analyst", icon: Sparkles, badge: "SQL" },
  { id: "datasets", label: "Datasets", icon: Database },
  { id: "reports", label: "Reports", icon: FileText },
  { id: "evaluation", label: "Evaluation", icon: CheckCircle2 },
];

interface WorkspaceShellProps {
  activePage: WorkspacePage;
  onNavigate: (page: WorkspacePage) => void;
  session: SessionInfo | null;
  deleting: boolean;
  onDeleteSession: () => void;
  queryCount: number;
  children: ReactNode;
}

export function WorkspaceShell({
  activePage,
  onNavigate,
  session,
  deleting,
  onDeleteSession,
  queryCount,
  children,
}: WorkspaceShellProps) {
  const [menuOpen, setMenuOpen] = useState(false);

  function go(page: WorkspacePage) {
    onNavigate(page);
    setMenuOpen(false);
  }

  return (
    <div className="flex min-h-screen bg-background">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-md focus:bg-card focus:px-3 focus:py-2 focus:text-sm focus:font-medium focus:text-foreground focus:shadow-md"
      >
        Skip to main content
      </a>
      {menuOpen && (
        <div
          className="fixed inset-0 z-30 bg-slate-950/50 backdrop-blur-xs lg:hidden"
          onClick={() => setMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      <aside
        id="workspace-sidebar"
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-64 flex-col bg-sidebar text-sidebar-foreground transition-transform duration-200 lg:static lg:translate-x-0",
          menuOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-14 items-center justify-between border-b border-sidebar-border px-4">
          <div className="flex items-center gap-2.5 font-semibold tracking-tight">
            <span className="flex size-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <BarChart3 className="size-4" />
            </span>
            <span className="text-sm">InsightAI</span>
          </div>
          <button
            type="button"
            onClick={() => setMenuOpen(false)}
            className="rounded-md p-1 text-sidebar-muted hover:bg-sidebar-accent hover:text-sidebar-foreground lg:hidden"
            aria-label="Close navigation"
          >
            <X className="size-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-4">
          <div className="mb-2 px-2 text-[11px] font-medium uppercase tracking-wider text-sidebar-muted">
            Workspace
          </div>
          <nav className="space-y-1" aria-label="Workspace navigation">
            {NAV_ITEMS.map(({ id, label, icon: Icon, badge }) => {
              const active = activePage === id;
              return (
                <button
                  key={id}
                  type="button"
                  aria-current={active ? "page" : undefined}
                  onClick={() => go(id)}
                  className={cn(
                    "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors cursor-pointer",
                    active
                      ? "bg-sidebar-accent text-sidebar-foreground"
                      : "text-sidebar-muted hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
                  )}
                >
                  <Icon className="size-4 shrink-0" />
                  <span className="flex-1 text-left">{label}</span>
                  {badge && (
                    <span className="rounded bg-primary/20 px-1.5 py-0.5 font-mono text-[10px] font-semibold text-blue-300">
                      {badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          <div className="mt-6 mb-2 px-2 text-[11px] font-medium uppercase tracking-wider text-sidebar-muted">
            Configuration
          </div>
          <nav className="space-y-1" aria-label="Settings navigation">
            <button
              type="button"
              aria-current={activePage === "settings" ? "page" : undefined}
              onClick={() => go("settings")}
              className={cn(
                "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm font-medium transition-colors cursor-pointer",
                activePage === "settings"
                  ? "bg-sidebar-accent text-sidebar-foreground"
                  : "text-sidebar-muted hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
              )}
            >
              <Settings className="size-4 shrink-0" />
              <span>AI Settings</span>
            </button>
          </nav>
        </div>

        <SidebarSessionPanel session={session} queryCount={queryCount} />
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-border bg-card/85 px-4 backdrop-blur-md lg:px-6">
          <div className="flex items-center gap-3">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="lg:hidden"
              aria-label="Toggle menu"
              aria-expanded={menuOpen}
              aria-controls="workspace-sidebar"
              onClick={() => setMenuOpen((prev) => !prev)}
            >
              <Menu className="size-4" />
            </Button>
            <div className="flex items-center gap-2 text-sm">
              <span className="text-muted-foreground">Workspace</span>
              <span className="text-border">/</span>
              <span className="font-medium text-foreground">{PAGE_LABELS[activePage]}</span>
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            size="sm"
            className="text-destructive hover:border-destructive/40 hover:bg-destructive/5 hover:text-destructive"
            disabled={deleting || !session}
            onClick={onDeleteSession}
          >
            <Trash2 className="size-3.5" />
            {deleting ? "Deleting…" : "Delete my data"}
          </Button>
        </header>

        <main
          id="main-content"
          tabIndex={-1}
          className="mx-auto w-full max-w-6xl flex-1 p-4 focus:outline-none lg:p-8"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
