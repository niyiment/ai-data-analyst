"use client";

import { useEffect, useState } from "react";
import { listEvalSets, startEvalRun } from "../api/eval-api";
import type { EvalRunDetail, GoldenSetSummary } from "../types/eval";

export function EvaluationView() {
  const [sets, setSets] = useState<GoldenSetSummary[]>([]);
  const [selectedSet, setSelectedSet] = useState("retail_sales");
  const [run, setRun] = useState<EvalRunDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const loaded = await listEvalSets();
        setSets(loaded);
        if (loaded.length > 0 && loaded[0]) {
          setSelectedSet(loaded[0].name);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not load evaluation sets.");
      }
    })();
  }, []);

  async function handleRun() {
    setBusy(true);
    setError(null);
    try {
      setRun(await startEvalRun(selectedSet));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Evaluation run failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-label="Evaluation">
      <div className="page-head">
        <div>
          <div className="eyebrow">Quality &amp; benchmarks</div>
          <h1>Evaluation</h1>
          <p>Run golden question sets to measure SQL accuracy, validator rejections, and latency.</p>
        </div>
        <div className="actions">
          <label htmlFor="eval-set-select" className="sr-only">
            Golden question set
          </label>
          <select
            id="eval-set-select"
            name="evalSet"
            className="select"
            value={selectedSet}
            onChange={(e) => setSelectedSet(e.target.value)}
            disabled={busy}
          >
            {sets.map((s) => (
              <option key={s.name} value={s.name}>
                {s.name} ({s.question_count} questions)
              </option>
            ))}
          </select>
          <button type="button" className="btn primary" disabled={busy} onClick={() => void handleRun()}>
            {busy ? "Running…" : "▶ Run evaluation"}
          </button>
        </div>
      </div>

      {error && (
        <div role="alert" className="alert-error">
          {error}
        </div>
      )}

      <div aria-live="polite">
        {run ? (
          <>
            <div className="metrics">
              <div className="metric">
                <div className="metric-top">
                  <span>Execution accuracy</span>
                  <span className="metric-icon green">✓</span>
                </div>
                <div className="metric-value">{Math.round(run.accuracy * 100)}%</div>
                <div className="metric-foot">
                  {run.correct_count} of {run.total_questions} passed
                </div>
              </div>
              <div className="metric">
                <div className="metric-top">
                  <span>Rejection rate</span>
                  <span className="metric-icon amber">!</span>
                </div>
                <div className="metric-value">{Math.round(run.rejection_rate * 100)}%</div>
                <div className="metric-foot">{run.rejected_count} blocked by validator</div>
              </div>
              <div className="metric">
                <div className="metric-top">
                  <span>p95 latency</span>
                  <span className="metric-icon">◷</span>
                </div>
                <div className="metric-value">{run.p95_latency_ms} ms</div>
                <div className="metric-foot">p50: {run.p50_latency_ms} ms</div>
              </div>
              <div className="metric">
                <div className="metric-top">
                  <span>Token usage</span>
                  <span className="metric-icon">✦</span>
                </div>
                <div className="metric-value">
                  {(run.total_tokens_in + run.total_tokens_out).toLocaleString()}
                </div>
                <div className="metric-foot">Model: {run.model}</div>
              </div>
            </div>

            <div className="panel">
              <div className="panel-head">
                <div>
                  <div className="panel-title">Question results ({run.set_name})</div>
                  <div className="panel-sub">Prompt {run.prompt_version}</div>
                </div>
              </div>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Question</th>
                      <th>Category</th>
                      <th>Difficulty</th>
                      <th>Outcome</th>
                      <th>Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {run.results.map((r) => (
                      <tr key={r.question_id}>
                        <td>{r.question_id}</td>
                        <td>{r.question}</td>
                        <td>{r.category}</td>
                        <td>{r.difficulty}</td>
                        <td>
                          <span className="status">{r.outcome}</span>
                        </td>
                        <td>{r.latency_ms} ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <div className="panel" style={{ padding: "32px", textAlign: "center" }}>
            <strong style={{ fontSize: "13px" }}>Ready to benchmark</strong>
            <p className="empty-note">
              Select a golden set above and click &ldquo;Run evaluation&rdquo; to inspect accuracy
              and validator safety.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
