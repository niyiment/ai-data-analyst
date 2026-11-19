"use client";

import { useState, type FormEvent } from "react";
import { InsightsAndReportActions } from "@/features/reports";
import { askQuestion } from "../api/query-api";
import type { QueryResult } from "../types/query";

interface QueryPanelProps {
  datasetId: string;
}

export function QueryPanel({ datasetId }: QueryPanelProps) {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResult | null>(null);

  async function runQuery(q: string, choice?: string) {
    setBusy(true);
    setError(null);
    try {
      setResult(await askQuestion(datasetId, q, choice));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Query failed.");
    } finally {
      setBusy(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (trimmed.length >= 2) {
      void runQuery(trimmed);
    }
  }

  return (
    <section
      aria-label="Ask a question"
      style={{
        padding: "1.25rem",
        border: "1px solid #d4d4d8",
        borderRadius: "8px",
        marginBottom: "2rem",
      }}
    >
      <h2>Ask a question</h2>
      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", gap: "0.75rem", marginTop: "0.5rem" }}
      >
        <label htmlFor="question-input" style={{ flex: 1 }}>
          <span className="sr-only">Natural-language question</span>
          <input
            id="question-input"
            type="text"
            placeholder="e.g. What is total revenue by region?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            disabled={busy}
            style={{ width: "100%", padding: "0.5rem" }}
          />
        </label>
        <button type="submit" disabled={busy || question.trim().length < 2}>
          {busy ? "Running…" : "Ask"}
        </button>
      </form>

      {error && (
        <p role="alert" style={{ color: "#b91c1c", marginTop: "0.75rem" }}>
          {error}
        </p>
      )}

      {result && result.status === "needs_clarification" && result.plan && (
        <div style={{ marginTop: "1rem" }}>
          <p>
            <strong>Clarification needed:</strong> {result.plan.clarifying_question}
          </p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.5rem" }}>
            {result.plan.clarification_options.map((opt) => (
              <button
                key={opt}
                type="button"
                disabled={busy}
                onClick={() => void runQuery(result.question, opt)}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      )}

      {result && result.status === "rejected" && (
        <div role="alert" style={{ color: "#b91c1c", marginTop: "1rem" }}>
          <strong>Query rejected by safety validator:</strong>
          <ul>
            {result.rejection_reasons.map((r, i) => (
              <li key={i}>
                <code>{r.rule}</code>: {r.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      {result && result.status === "succeeded" && (
        <div style={{ marginTop: "1rem" }}>
          {result.plan && (
            <p>
              <strong>Plan:</strong> {result.plan.intent}
            </p>
          )}
          {result.generated_sql && (
            <details style={{ marginBottom: "0.75rem" }}>
              <summary>Generated SQL</summary>
              <pre style={{ overflowX: "auto", padding: "0.5rem", background: "#f4f4f5" }}>
                <code>{result.generated_sql}</code>
              </pre>
            </details>
          )}
          <p>
            Showing {result.row_count} rows{result.truncated ? " (truncated at row limit)" : ""}.
          </p>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {result.columns.map((col) => (
                    <th key={col} align="left">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.rows.map((row, idx) => (
                  <tr key={idx} style={{ borderTop: "1px solid #e4e4e7" }}>
                    {result.columns.map((col) => (
                      <td key={col}>{String(row[col] ?? "")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <InsightsAndReportActions queryRunId={result.id} question={result.question} />
        </div>
      )}
    </section>
  );
}
