"use client";

import { InsightsAndReportActions, type ReportSummary } from "@/features/reports";
import type { QueryResult } from "../types/query";

interface QueryResultBubbleProps {
  result: QueryResult;
  busy: boolean;
  onClarify: (question: string, option: string) => void;
  onReportCreated?: (report: ReportSummary) => void;
}

export function QueryResultBubble({
  result,
  busy,
  onClarify,
  onReportCreated,
}: QueryResultBubbleProps) {
  if (result.status === "needs_clarification" && result.plan) {
    return (
      <div className="message">
        <div className="message-avatar">✦</div>
        <div className="bubble">
          <p>
            <strong>Clarification needed:</strong> {result.plan.clarifying_question}
          </p>
          <div className="suggestions">
            {result.plan.clarification_options.map((opt) => (
              <button
                key={opt}
                type="button"
                disabled={busy}
                onClick={() => onClarify(result.question, opt)}
              >
                {opt}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (result.status === "rejected") {
    return (
      <div className="message">
        <div className="message-avatar">!</div>
        <div className="bubble" role="alert">
          <p>
            <strong>Query rejected by safety validator</strong>
          </p>
          <ul style={{ margin: "4px 0 0", paddingLeft: "18px" }}>
            {result.rejection_reasons.map((r, i) => (
              <li key={i}>
                <code>{r.rule}</code>: {r.message}
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="message">
      <div className="message-avatar">✦</div>
      <div className="bubble">
        {result.plan && (
          <p>
            <strong>Plan:</strong> {result.plan.intent}
          </p>
        )}
        <div className="result-mini">
          <div className="result-mini-head">
            <span>Query result</span>
            <span style={{ color: "#315eea" }}>
              {result.row_count} rows{result.truncated ? " (truncated)" : ""}
            </span>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  {result.columns.map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {result.rows.map((row, idx) => (
                  <tr key={idx}>
                    {result.columns.map((col) => (
                      <td key={col}>{String(row[col] ?? "")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {result.generated_sql && <div className="sql">{result.generated_sql}</div>}

        <InsightsAndReportActions
          queryRunId={result.id}
          question={result.question}
          onReportCreated={onReportCreated}
        />
      </div>
    </div>
  );
}
