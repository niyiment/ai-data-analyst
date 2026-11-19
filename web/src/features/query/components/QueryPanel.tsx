"use client";

import { useEffect, useState, type FormEvent } from "react";
import type { ReportSummary } from "@/features/reports";
import { askQuestion } from "../api/query-api";
import type { QueryResult } from "../types/query";
import { QueryResultBubble } from "./QueryResultBubble";

const SUGGESTIONS = ["Show total rows per table", "Summarize top categories", "Compare by region"];

interface QueryPanelProps {
  datasetId: string;
  datasetName?: string;
  rowCount?: number;
  columnCount?: number;
  initialQuestion?: string | null;
  onInitialQuestionHandled?: () => void;
  onQueryCompleted?: () => void;
  onReportCreated?: (report: ReportSummary) => void;
  onViewSchema?: () => void;
}

export function QueryPanel({
  datasetId,
  datasetName = "Active dataset",
  rowCount = 0,
  columnCount = 0,
  initialQuestion,
  onInitialQuestionHandled,
  onQueryCompleted,
  onReportCreated,
  onViewSchema,
}: QueryPanelProps) {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<QueryResult[]>([]);

  async function runQuery(q: string, choice?: string) {
    setBusy(true);
    setError(null);
    try {
      const res = await askQuestion(datasetId, q, choice);
      setHistory((prev) => [...prev, res]);
      onQueryCompleted?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (initialQuestion && initialQuestion.trim().length >= 2) {
      void runQuery(initialQuestion.trim());
      onInitialQuestionHandled?.();
    }
  }, [initialQuestion]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (trimmed.length >= 2) {
      setQuestion("");
      void runQuery(trimmed);
    }
  }

  return (
    <section aria-label="AI Analyst">
      <div className="page-head">
        <div>
          <div className="eyebrow">Natural language analytics</div>
          <h1>AI Analyst</h1>
          <p>Ask questions about your dataset and inspect the validated read-only SQL.</p>
        </div>
        <div className="actions">
          <button type="button" className="btn" onClick={() => setHistory([])}>
            ↻ Clear conversation
          </button>
          {onViewSchema && (
            <button type="button" className="btn primary" onClick={onViewSchema}>
              ⌘ View schema
            </button>
          )}
        </div>
      </div>

      <div className="analyst-layout">
        <div className="panel chat-panel">
          <div className="panel-head">
            <div>
              <div className="panel-title">{datasetName}</div>
              <div className="panel-sub">Read-only SQL pipeline · AST validated</div>
            </div>
            <span className="status">Connected</span>
          </div>

          <div className="chat-messages">
            <div className="message">
              <div className="message-avatar">✦</div>
              <div className="bubble">
                <p>
                  <strong>Welcome to AI Analyst.</strong>
                </p>
                <p>
                  Ask a question in plain English. I will generate a safe, read-only SQL query,
                  validate it, and return the results.
                </p>
              </div>
            </div>

            {history.map((item) => (
              <div key={item.id} style={{ display: "grid", gap: "14px" }}>
                <div className="message user">
                  <div className="message-avatar">You</div>
                  <div className="bubble">{item.question}</div>
                </div>
                <QueryResultBubble
                  result={item}
                  busy={busy}
                  onClarify={(q, opt) => void runQuery(q, opt)}
                  onReportCreated={onReportCreated}
                />
              </div>
            ))}

            {error && (
              <div role="alert" className="alert-error">
                {error}
              </div>
            )}
          </div>

          <div className="chat-compose">
            <form className="compose-box" onSubmit={handleSubmit}>
              <span style={{ color: "#8b98ab" }} aria-hidden="true">
                ✦
              </span>
              <input
                id="question-input"
                type="text"
                placeholder="Ask a question about your data..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={busy}
                aria-label="Natural-language question"
              />
              <button type="submit" disabled={busy || question.trim().length < 2} aria-label="Ask">
                {busy ? "…" : "➜"}
              </button>
            </form>
            <div className="suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} type="button" onClick={() => setQuestion(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>

        <aside className="panel context-panel">
          <h3>Analysis context</h3>
          <div className="context-dataset">
            <span className="file-icon">▤</span>
            <div>
              <b>{datasetName}</b>
              <small>
                {rowCount.toLocaleString()} rows · {columnCount} columns
              </small>
            </div>
          </div>
          <h3 style={{ marginTop: "22px" }}>Dataset profile</h3>
          <div className="field">
            <span>Rows indexed</span>
            <b>{rowCount.toLocaleString()}</b>
          </div>
          <div className="field">
            <span>Columns</span>
            <b>{columnCount}</b>
          </div>
          <div className="field">
            <span>Row cap</span>
            <b>1,000 rows</b>
          </div>
          <div className="field">
            <span>Timeout</span>
            <b>10 seconds</b>
          </div>
          <p style={{ fontSize: "10px", color: "#929daf", lineHeight: 1.6, marginTop: "18px" }}>
            AI-generated SQL is validated by SQLGlot before execution on a read-only PostgreSQL
            role.
          </p>
        </aside>
      </div>
    </section>
  );
}
