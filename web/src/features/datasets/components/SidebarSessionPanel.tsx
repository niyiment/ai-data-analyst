"use client";

import NumberFlow from "@number-flow/react";
import type { SessionInfo } from "@/features/sessions";

const HOURLY_QUESTION_LIMIT = 30;

interface SidebarSessionPanelProps {
  session: SessionInfo | null;
  queryCount: number;
}

export function SidebarSessionPanel({ session, queryCount }: SidebarSessionPanelProps) {
  const usagePct = Math.min(100, Math.round((queryCount / HOURLY_QUESTION_LIMIT) * 100));
  const expiresLabel = session
    ? new Date(session.expires_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "Starting…";

  return (
    <div className="space-y-3 border-t border-sidebar-border p-3">
      <div className="rounded-lg bg-sidebar-accent/60 p-3">
        <div className="flex items-center justify-between text-xs font-medium">
          <span id="session-quota-label" className="text-sidebar-foreground">
            Session quota
          </span>
          <span className="font-mono text-sidebar-muted">
            <NumberFlow value={usagePct} suffix="%" />
          </span>
        </div>
        <p className="mt-1 text-[11px] text-sidebar-muted">
          {queryCount} of {HOURLY_QUESTION_LIMIT} hourly queries used
        </p>
        <div
          role="progressbar"
          aria-labelledby="session-quota-label"
          aria-valuenow={usagePct}
          aria-valuemin={0}
          aria-valuemax={100}
          className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-slate-800"
        >
          <div
            className="h-full rounded-full bg-blue-500 transition-all duration-300"
            style={{ width: `${usagePct}%` }}
          />
        </div>
      </div>

      <div className="flex items-center gap-2.5 px-1">
        <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/20 text-xs font-semibold text-blue-300">
          AI
        </div>
        <div className="min-w-0">
          <div className="truncate text-xs font-medium text-sidebar-foreground">
            Anonymous session
          </div>
          <div className="truncate text-[11px] text-sidebar-muted">Auto-deletes {expiresLabel}</div>
        </div>
      </div>
    </div>
  );
}
