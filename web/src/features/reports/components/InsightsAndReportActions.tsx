"use client";

import { useState } from "react";
import {
  createReport,
  generateInsights,
  type InsightsData,
  type ReportSummary,
} from "../api/report-api";

interface InsightsAndReportActionsProps {
  queryRunId: string;
  question: string;
}

export function InsightsAndReportActions({ queryRunId, question }: InsightsAndReportActionsProps) {
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [report, setReport] = useState<ReportSummary | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerateInsights() {
    setBusy(true);
    setError(null);
    try {
      setInsights(await generateInsights(queryRunId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not generate insights.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateReport() {
    setBusy(true);
    setError(null);
    try {
      setReport(await createReport(question, queryRunId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create report.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ marginTop: "1rem" }}>
      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
        <button type="button" disabled={busy} onClick={() => void handleGenerateInsights()}>
          {busy ? "Working…" : "Generate insights"}
        </button>
        <button type="button" disabled={busy} onClick={() => void handleCreateReport()}>
          Pin to report
        </button>
        {report && (
          <>
            <a href={`/api/v1/reports/${report.id}/export?format=html`} download>
              Download HTML
            </a>
            <a href={`/api/v1/reports/${report.id}/export?format=pdf`} download>
              Download PDF
            </a>
          </>
        )}
      </div>

      {error && (
        <p role="alert" style={{ color: "#b91c1c", marginTop: "0.5rem" }}>
          {error}
        </p>
      )}

      {insights && (
        <section aria-label="Insights" style={{ marginTop: "0.75rem" }}>
          <p>
            <strong>Summary:</strong> {insights.summary}
          </p>
          {insights.key_findings.length > 0 && (
            <ul>
              {insights.key_findings.map((finding, idx) => (
                <li key={idx}>{finding}</li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
