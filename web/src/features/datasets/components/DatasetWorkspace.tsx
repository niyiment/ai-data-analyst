"use client";

import { useEffect, useState } from "react";
import { QueryPanel } from "@/features/query";
import {
  SessionBanner,
  createSession,
  deleteMySession,
  getMySession,
  type SessionInfo,
} from "@/features/sessions";
import { loadSampleDataset, updateDatasetColumn, uploadDatasetFile } from "../api/dataset-api";
import type { DatasetDetail } from "../types/dataset";
import { SchemaReviewTable } from "./SchemaReviewTable";
import { UploadPanel } from "./UploadPanel";

export function DatasetWorkspace() {
  const [session, setSession] = useState<SessionInfo | null>(null);
  const [dataset, setDataset] = useState<DatasetDetail | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const existing = await getMySession();
        setSession(existing);
      } catch {
        try {
          const created = await createSession();
          setSession(created);
        } catch (err) {
          setError(err instanceof Error ? err.message : "Could not start session.");
        }
      }
    })();
  }, []);

  async function handleUpload(file: File) {
    setBusy(true);
    setError(null);
    try {
      setDataset(await uploadDatasetFile(file));
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
      setDataset(await loadSampleDataset("retail_sales"));
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
      setDataset({
        ...dataset,
        tables: dataset.tables.map((t) => ({
          ...t,
          columns: t.columns.map((c) => (c.id === columnId ? updated : c)),
        })),
      });
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
      setSession(await createSession());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete session.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: "960px", margin: "2rem auto", padding: "0 1rem" }}>
      <SessionBanner session={session} deleting={busy} onDeleteSession={handleDeleteSession} />
      {error && (
        <div role="alert" style={{ color: "#b91c1c", marginBottom: "1rem" }}>
          {error}
        </div>
      )}
      <UploadPanel busy={busy} onUploadFile={handleUpload} onLoadSample={handleLoadSample} />
      {dataset && (
        <>
          <QueryPanel datasetId={dataset.id} />
          <section aria-label="Schema review">
            <h2>Schema Review: {dataset.original_filename}</h2>
            {dataset.tables.map((table) => (
              <SchemaReviewTable key={table.id} table={table} onUpdateColumn={handleUpdateColumn} />
            ))}
          </section>
        </>
      )}
    </div>
  );
}
