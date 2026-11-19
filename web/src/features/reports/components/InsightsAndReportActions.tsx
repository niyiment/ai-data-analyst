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
  onReportCreated?: (report: ReportSummary) => void;
}

export function InsightsAndReportActions({
  queryRunId,
  question,
  onReportCreated,
}: InsightsAndReportActionsProps) {
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
      const created = await createReport(question, queryRunId);
      setReport(created);
      onReportCreated?.(created);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create report.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ marginTop: "12px" }}>
      <div className="actions">
        <button type="button" className="btn" disabled={busy} onClick={() => void handleGenerateInsights()}>
          {busy ? "Working…" : "✦ Generate insights"}
        </button>
        <button type="button" className="btn" disabled={busy} onClick={() => void handleCreateReport()}>
          ＋ Pin to report
        </button>
        {report && (
          <>
            <a className="btn primary" href={`/api/v1/reports/${report.id}/export?format=html`} download>
              ⇩ HTML
            </a>
            <a className="btn primary" href={`/api/v1/reports/${report.id}/export?format=pdf`} download>
              ⇩ PDF
            </a>
          </>
        )}
      </div>

      {error && (
        <p role="alert" className="alert-error" style={{ marginTop: "10px", marginBottom: 0 }}>
          {error}
        </p>
      )}

      {insights && (
        <section className="insight-card" aria-label="Insights">
          <div className="insight-head">✦ AI Insights</div>
          <p>{insights.summary}</p>
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
