"use client";

import { Database, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { EvaluationView } from "@/features/evaluation";
import { QueryPanel } from "@/features/query";
import { ReportsView, type ReportSummary } from "@/features/reports";
import { SettingsView } from "@/features/settings";
import {
  createSession,
  deleteMySession,
  getMySession,
  type SessionInfo,
} from "@/features/sessions";
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

  useEffect(() => {
    void (async () => {
      try {
        setSession(await getMySession());
      } catch {
        try {
          setSession(await createSession());
        } catch (err) {
          toast.error(err instanceof Error ? err.message : "Could not start session.");
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
    try {
      const loaded = await uploadDatasetFile(file);
      addDataset(loaded);
      toast.success(`Uploaded ${loaded.original_filename}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  async function handleLoadSample() {
    setBusy(true);
    try {
      const loaded = await loadSampleDataset("retail_sales");
      addDataset(loaded);
      toast.success("Loaded Retail Sales sample dataset");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not load sample dataset.");
    } finally {
      setBusy(false);
    }
  }

  async function handleUpdateColumn(
    columnId: string,
    payload: { column_name?: string; pg_type?: string },
  ) {
    if (!dataset) return;
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
      toast.success(`Updated column ${updated.column_name}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not update column.");
    }
  }

  async function handleDeleteSession() {
    setBusy(true);
    try {
      await deleteMySession();
      setDataset(null);
      setDatasets([]);
      setReports([]);
      setQueryCount(0);
      setSession(await createSession());
      toast.success("Session data deleted and fresh session started");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not delete session.");
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
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-14 text-center">
              <div className="mb-4 flex size-12 items-center justify-center rounded-xl bg-muted text-muted-foreground">
                <Database className="size-6" />
              </div>
              <h2 className="text-lg font-semibold">No dataset selected</h2>
              <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                Upload a CSV or Excel file, or load the Retail Sales sample to start asking
                questions.
              </p>
              <div className="mt-5 flex flex-wrap justify-center gap-2.5">
                <Button type="button" onClick={() => setActivePage("datasets")}>
                  <Database className="size-4" />
                  Go to Datasets
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={busy}
                  onClick={() => void handleLoadSample()}
                >
                  <Sparkles className="size-4" />
                  Load Retail Sales sample
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}

      {activePage === "datasets" && (
        <section aria-label="Datasets library" className="space-y-6">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-primary">
              Your data library
            </p>
            <h1 className="mt-1 text-2xl font-semibold tracking-tight">Datasets</h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Upload CSV or Excel files, inspect inferred schemas, and override column types.
            </p>
          </div>
          <UploadPanel
            busy={busy}
            onUploadFile={handleUpload}
            onLoadSample={() => void handleLoadSample()}
          />
          {dataset && (
            <section aria-label="Schema review" className="space-y-4">
              <h2 className="text-base font-semibold tracking-tight">
                Schema Review:{" "}
                <span className="font-mono text-primary">{dataset.original_filename}</span>
              </h2>
              {dataset.tables.map((table) => (
                <SchemaReviewTable
                  key={table.id}
                  table={table}
                  onUpdateColumn={handleUpdateColumn}
                />
              ))}
            </section>
          )}
        </section>
      )}

      {activePage === "reports" && (
        <ReportsView reports={reports} onGoToAnalyst={() => setActivePage("analyst")} />
      )}

      {activePage === "evaluation" && <EvaluationView />}

      {activePage === "settings" && <SettingsView />}
    </WorkspaceShell>
  );
}
