"use client";

import type { SessionInfo } from "../types/session";

interface SessionBannerProps {
  session: SessionInfo | null;
  deleting: boolean;
  onDeleteSession: () => void;
}

export function SessionBanner({ session, deleting, onDeleteSession }: SessionBannerProps) {
  if (!session) {
    return (
      <section aria-label="Session status">
        <p>Starting anonymous session…</p>
      </section>
    );
  }

  const expiresLabel = new Date(session.expires_at).toLocaleString();

  return (
    <section
      aria-label="Session status"
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "0.75rem 1rem",
        border: "1px solid #d4d4d8",
        borderRadius: "8px",
        marginBottom: "1.5rem",
      }}
    >
      <div>
        <strong>Anonymous session active</strong> — data auto-deletes at {expiresLabel}
      </div>
      <button type="button" onClick={onDeleteSession} disabled={deleting}>
        {deleting ? "Deleting…" : "Delete my data now"}
      </button>
    </section>
  );
}
