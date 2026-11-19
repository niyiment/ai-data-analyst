"use client";

import type { ReportSummary } from "../api/report-api";

interface ReportsViewProps {
  reports: ReportSummary[];
  onGoToAnalyst: () => void;
}

export function ReportsView({ reports, onGoToAnalyst }: ReportsViewProps) {
  return (
    <section aria-label="Reports">
      <div className="page-head">
        <div>
          <div className="eyebrow">Your generated insights</div>
          <h1>Reports</h1>
          <p>Review and export your pinned analytical reports as PDF or HTML.</p>
        </div>
        <div className="actions">
          <button type="button" className="btn primary" onClick={onGoToAnalyst}>
            ✦ New analysis
          </button>
        </div>
      </div>

      {reports.map((report) => (
        <div key={report.id} className="panel report-card">
          <div>
            <h3>{report.title}</h3>
            <p>Pinned query run with validated SQL, results, and insights.</p>
            <div className="report-meta">
              <span>◷ {new Date(report.created_at).toLocaleString()}</span>
            </div>
          </div>
          <div className="actions">
            <a className="btn" href={`/api/v1/reports/${report.id}/export?format=html`} download>
              ⇩ HTML
            </a>
            <a className="btn primary" href={`/api/v1/reports/${report.id}/export?format=pdf`} download>
              ⇩ PDF
            </a>
          </div>
        </div>
      ))}

      <div className="panel" style={{ padding: "28px", textAlign: "center", marginTop: "16px" }}>
        <div style={{ fontSize: "24px", color: "#9aace9" }}>▤</div>
        <strong style={{ fontSize: "13px" }}>
          {reports.length === 0 ? "No reports pinned yet" : "Reports that tell the whole story"}
        </strong>
        <p className="empty-note">
          Ask a question in AI Analyst and click &ldquo;Pin to report&rdquo; to export as PDF or HTML.
        </p>
      </div>
    </section>
  );
}
