"use client";

import { useState, type FormEvent } from "react";
import type { DatasetDetail } from "../types/dataset";
import type { WorkspacePage } from "./WorkspaceShell";

interface OverviewViewProps {
  datasets: DatasetDetail[];
  queryCount: number;
  reportCount: number;
  onNavigate: (page: WorkspacePage) => void;
  onSelectDataset: (dataset: DatasetDetail) => void;
  onQuickAsk: (question: string) => void;
}

export function OverviewView({
  datasets,
  queryCount,
  reportCount,
  onNavigate,
  onSelectDataset,
  onQuickAsk,
}: OverviewViewProps) {
  const [quickQuestion, setQuickQuestion] = useState("");
  const totalRows = datasets.reduce(
    (sum, ds) => sum + ds.tables.reduce((tSum, t) => tSum + t.row_count, 0),
    0,
  );

  function handleQuickSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = quickQuestion.trim();
    if (trimmed.length >= 2) {
      onQuickAsk(trimmed);
      setQuickQuestion("");
    }
  }

  return (
    <section aria-label="Workspace overview">
      <div className="page-head">
        <div>
          <div className="eyebrow">Your analytics workspace</div>
          <h1>Analytics Overview</h1>
          <p>Upload spreadsheets, inspect inferred schemas, and run validated read-only SQL.</p>
        </div>
        <div className="actions">
          <button type="button" className="btn" onClick={() => onNavigate("datasets")}>
            ＋ Upload dataset
          </button>
          <button type="button" className="btn primary" onClick={() => onNavigate("analyst")}>
            ✦ Ask your data
          </button>
        </div>
      </div>

      <div className="metrics">
        <div className="metric">
          <div className="metric-top">
            <span>Datasets uploaded</span>
            <span className="metric-icon">▤</span>
          </div>
          <div className="metric-value">{datasets.length}</div>
          <div className="metric-foot">
            <span className="up">Max 3</span> per anonymous session
          </div>
        </div>
        <div className="metric">
          <div className="metric-top">
            <span>Questions answered</span>
            <span className="metric-icon green">✓</span>
          </div>
          <div className="metric-value">{queryCount}</div>
          <div className="metric-foot">Validated read-only SQL</div>
        </div>
        <div className="metric">
          <div className="metric-top">
            <span>Reports generated</span>
            <span className="metric-icon amber">📄</span>
          </div>
          <div className="metric-value">{reportCount}</div>
          <div className="metric-foot">Exportable as PDF &amp; HTML</div>
        </div>
        <div className="metric">
          <div className="metric-top">
            <span>Rows indexed</span>
            <span className="metric-icon">↗</span>
          </div>
          <div className="metric-value">{totalRows.toLocaleString()}</div>
          <div className="metric-foot">Across active session tables</div>
        </div>
      </div>

      <div className="bottom-grid">
        <div className="panel">
          <div className="panel-head">
            <div>
              <div className="panel-title">Recent datasets</div>
              <div className="panel-sub">Your uploaded files in this 24-hour session</div>
            </div>
            <button type="button" className="btn" onClick={() => onNavigate("datasets")}>
              Manage datasets →
            </button>
          </div>
          <div className="table-wrap">
            {datasets.length === 0 ? (
              <div style={{ padding: "24px 18px" }} className="empty-note">
                No datasets uploaded yet. Upload a CSV/XLSX file or load a sample dataset to begin.
              </div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Dataset</th>
                    <th>Tables</th>
                    <th>Rows</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {datasets.map((ds) => {
                    const rows = ds.tables.reduce((s, t) => s + t.row_count, 0);
                    return (
                      <tr
                        key={ds.id}
                        style={{ cursor: "pointer" }}
                        onClick={() => {
                          onSelectDataset(ds);
                          onNavigate("analyst");
                        }}
                      >
                        <td>
                          <div className="file-cell">
                            <span className="file-icon">▤</span>
                            {ds.original_filename}
                          </div>
                        </td>
                        <td>{ds.tables.length}</td>
                        <td>{rows.toLocaleString()}</td>
                        <td>
                          <span className="status">{ds.status}</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="panel">
          <div className="panel-head">
            <div>
              <div className="panel-title">Safety &amp; privacy</div>
              <div className="panel-sub">Built-in guardrails for every query</div>
            </div>
          </div>
          <div className="activity">
            <div className="activity-item">
              <span className="activity-symbol">✦</span>
              <div className="activity-text">
                <b>SQLGlot AST Validator</b>
                <br />
                Single SELECT only, function &amp; table allowlists
              </div>
            </div>
            <div className="activity-item">
              <span className="activity-symbol green">✓</span>
              <div className="activity-text">
                <b>Read-only execution</b>
                <br />
                Dedicated PostgreSQL role with row &amp; time limits
              </div>
            </div>
            <div className="activity-item">
              <span className="activity-symbol">◷</span>
              <div className="activity-text">
                <b>24-hour auto-deletion</b>
                <br />
                Isolated per-dataset schema dropped automatically
              </div>
            </div>
          </div>
        </div>
      </div>

      <form className="quick-ask" onSubmit={handleQuickSubmit}>
        <div className="spark" aria-hidden="true">
          ✦
        </div>
        <div className="quick-copy">
          <strong>Have a question about your data?</strong>
          <p>Ask in plain English. Get validated SQL, tables, charts, and insights in seconds.</p>
        </div>
        <div className="ask-box">
          <input
            type="text"
            value={quickQuestion}
            onChange={(e) => setQuickQuestion(e.target.value)}
            placeholder="e.g. Which region had the highest sales?"
            aria-label="Quick question"
          />
          <button type="submit" aria-label="Ask">
            ➜
          </button>
        </div>
      </form>
    </section>
  );
}
