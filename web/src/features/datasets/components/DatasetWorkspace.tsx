"use client";

import { useEffect, useState } from "react";
import { QueryPanel } from "@/features/query";
import { ReportsView, type ReportSummary } from "@/features/reports";
import { createSession, deleteMySession, getMySession, type SessionInfo } from "@/features/sessions";
import { loadSampleDataset, updateDatasetColumn, uploadDatasetFile } from "../api/dataset-api";
import type { DatasetDetail } from "../types/dataset";
import { OverviewView } from "./OverviewView";
import { SchemaReviewTable } from "./SchemaReviewTable";
import { UploadPanel } from "./UploadPanel";
import { WorkspaceShell, type WorkspacePage } from "./WorkspaceShell";

export function DatasetWorkspace() {
  const [activePage, setActivePage] = useState<WorkspacePage>("overview");
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [datasets, setDatasets] = useState<DatasetDetail[]>([]);
  const [dataset, setDataset] = useState<DatasetDetail | null>(null);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [queryCount, setQueryCount] = useState(0);
  const [pendingQuestion, setPendingQuestion] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        setSession(await getMySession());
      } catch {
        try {
          setSession(await createSession());
        } catch (err) {
          setError(err instanceof Error ? err.message : "Could not start session.");
        }
      }
    })();
  }, []);

  function addDataset(loaded: DatasetDetail) {
    setDataset(loaded);
    setDatasets((prev) => [loaded, ...prev.filter((d) => d.id !== loaded.id)]);
  }

  async function handleUpload(file: File) {
    setBusy(true);
    setError(null);
    try {
      addDataset(await uploadDatasetFile(file));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleLoadSample() {
    setBusy(true);
    setError(null);
    try {
      addDataset(await loadSampleDataset("retail_sales"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load sample dataset.");
    } finally {
      setBusy(false);
    }
  }

  async function handleUpdateColumn(
    columnId: string,
    payload: { column_name?: string; pg_type?: string },
  ) {
    if (!dataset) return;
    setError(null);
    try {
      const updated = await updateDatasetColumn(dataset.id, columnId, payload);
      const next: DatasetDetail = {
        ...dataset,
        tables: dataset.tables.map((t) => ({
          ...t,
          columns: t.columns.map((c) => (c.id === columnId ? updated : c)),
        })),
      };
      addDataset(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update column.");
    }
  }

  async function handleDeleteSession() {
    setBusy(true);
    setError(null);
    try {
      await deleteMySession();
      setDataset(null);
      setDatasets([]);
      setReports([]);
      setQueryCount(0);
      setSession(await createSession());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete session.");
    } finally {
      setBusy(false);
    }
  }

  const activeRows = dataset?.tables.reduce((s, t) => s + t.row_count, 0) ?? 0;
  const activeCols = dataset?.tables.reduce((s, t) => s + t.columns.length, 0) ?? 0;

  return (
    <WorkspaceShell
      activePage={activePage}
      onNavigate={setActivePage}
      session={session}
      deleting={busy}
      onDeleteSession={() => void handleDeleteSession()}
      queryCount={queryCount}
    >
      {error && (
        <div role="alert" className="alert-error">
          {error}
        </div>
      )}

      {activePage === "overview" && (
        <OverviewView
          datasets={datasets}
          queryCount={queryCount}
          reportCount={reports.length}
          onNavigate={setActivePage}
          onSelectDataset={setDataset}
          onQuickAsk={(q) => {
            setPendingQuestion(q);
            setActivePage(dataset ? "analyst" : "datasets");
          }}
        />
      )}

      {activePage === "analyst" &&
        (dataset ? (
          <QueryPanel
            datasetId={dataset.id}
            datasetName={dataset.original_filename}
            rowCount={activeRows}
            columnCount={activeCols}
            initialQuestion={pendingQuestion}
            onInitialQuestionHandled={() => setPendingQuestion(null)}
            onQueryCompleted={() => setQueryCount((c) => c + 1)}
            onReportCreated={(r) => setReports((prev) => [r, ...prev])}
            onViewSchema={() => setActivePage("datasets")}
          />
        ) : (
          <div className="panel" style={{ padding: "36px", textAlign: "center" }}>
            <h2 style={{ marginTop: 0 }}>No dataset selected</h2>
            <p className="empty-note">Upload a CSV/XLSX file or load the Retail Sales sample first.</p>
            <div className="actions" style={{ justifyContent: "center", marginTop: "16px" }}>
              <button type="button" className="btn primary" onClick={() => setActivePage("datasets")}>
                Go to Datasets
              </button>
              <button type="button" className="btn" disabled={busy} onClick={() => void handleLoadSample()}>
                Load Retail Sales sample
              </button>
            </div>
          </div>
        ))}

      {activePage === "datasets" && (
        <section aria-label="Datasets library">
          <div className="page-head">
            <div>
              <div className="eyebrow">Your data library</div>
              <h1>Datasets</h1>
              <p>Upload CSV or Excel files, inspect inferred schemas, and override column types.</p>
            </div>
          </div>
          <UploadPanel busy={busy} onUploadFile={handleUpload} onLoadSample={() => void handleLoadSample()} />
          {dataset && (
            <section aria-label="Schema review" style={{ marginTop: "24px" }}>
              <h2 style={{ fontSize: "16px", margin: "0 0 6px" }}>
                Schema Review: {dataset.original_filename}
              </h2>
              {dataset.tables.map((table) => (
                <SchemaReviewTable key={table.id} table={table} onUpdateColumn={handleUpdateColumn} />
              ))}
            </section>
          )}
        </section>
      )}

      {activePage === "reports" && (
        <ReportsView reports={reports} onGoToAnalyst={() => setActivePage("analyst")} />
      )}
    </WorkspaceShell>
  );
}
