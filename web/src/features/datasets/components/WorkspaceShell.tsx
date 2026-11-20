"use client";

import { useState, type ReactNode } from "react";
import type { SessionInfo } from "@/features/sessions";

export type WorkspacePage = "overview" | "analyst" | "datasets" | "reports" | "evaluation";

const PAGE_LABELS: Record<WorkspacePage, string> = {
  overview: "Overview",
  analyst: "AI Analyst",
  datasets: "Datasets",
  reports: "Reports",
  evaluation: "Evaluation",
};

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

  const usagePct = Math.min(100, Math.round((queryCount / 30) * 100));
  const expiresLabel = session
    ? new Date(session.expires_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "Starting…";

  return (
    <div className="app">
      <aside className={`sidebar${menuOpen ? " open" : ""}`}>
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M4 18V9m5 9V5m5 13v-6m5 6V3" />
            </svg>
          </span>
          InsightAI
        </div>

        <div className="workspace-label">Workspace</div>
        <nav className="nav" aria-label="Main navigation">
          <button
            type="button"
            className={activePage === "overview" ? "active" : ""}
            onClick={() => go("overview")}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <rect x="3" y="3" width="8" height="8" rx="2" />
              <rect x="13" y="3" width="8" height="5" rx="2" />
              <rect x="13" y="10" width="8" height="11" rx="2" />
              <rect x="3" y="13" width="8" height="8" rx="2" />
            </svg>
            Overview
          </button>
          <button
            type="button"
            className={activePage === "analyst" ? "active" : ""}
            onClick={() => go("analyst")}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M4 5h16M4 12h10M4 19h7" />
              <circle cx="18" cy="15" r="3" />
              <path d="m20.2 17.2 1.8 1.8" />
            </svg>
            AI Analyst<span className="count">SQL</span>
          </button>
          <button
            type="button"
            className={activePage === "datasets" ? "active" : ""}
            onClick={() => go("datasets")}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <ellipse cx="12" cy="5" rx="8" ry="3" />
              <path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3" />
            </svg>
            Datasets
          </button>
          <button
            type="button"
            className={activePage === "reports" ? "active" : ""}
            onClick={() => go("reports")}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M6 3h9l4 4v14H6z" />
              <path d="M14 3v5h5M9 13h7M9 17h7" />
            </svg>
            Reports
          </button>
          <button
            type="button"
            className={activePage === "evaluation" ? "active" : ""}
            onClick={() => go("evaluation")}
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
            Evaluation
          </button>
        </nav>

        <div className="side-bottom">
          <div className="usage">
            <div className="usage-top">
              <span>Session quota</span>
              <span>{usagePct}%</span>
            </div>
            <p>{queryCount} of 30 hourly queries used</p>
            <div className="bar">
              <span style={{ width: `${usagePct}%` }} />
            </div>
          </div>

          <div className="profile">
            <div className="avatar">AI</div>
            <div>
              <strong>Anonymous session</strong>
              <small>Auto-deletes {expiresLabel}</small>
            </div>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <button
              type="button"
              className="icon-btn mobile-menu"
              aria-label="Toggle menu"
              onClick={() => setMenuOpen((prev) => !prev)}
            >
              ☰
            </button>
            <div className="crumb">
              Workspace <span style={{ padding: "0 6px", color: "#c0c8d4" }}>/</span>{" "}
              <b>{PAGE_LABELS[activePage]}</b>
            </div>
          </div>

          <div className="top-actions">
            <button
              type="button"
              className="btn danger"
              disabled={deleting || !session}
              onClick={onDeleteSession}
            >
              {deleting ? "Deleting…" : "Delete my data now"}
            </button>
            <div className="top-avatar" title="Anonymous session">
              AI
            </div>
          </div>
        </header>

        <div className="content">{children}</div>
      </main>
    </div>
  );
}
