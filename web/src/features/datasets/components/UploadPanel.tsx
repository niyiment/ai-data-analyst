"use client";

import type { ChangeEvent } from "react";

interface UploadPanelProps {
  busy: boolean;
  onUploadFile: (file: File) => void;
  onLoadSample: () => void;
}

export function UploadPanel({ busy, onUploadFile, onLoadSample }: UploadPanelProps) {
  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      onUploadFile(file);
      event.target.value = "";
    }
  }

  return (
    <section
      aria-label="Upload dataset"
      style={{
        padding: "1.25rem",
        border: "1px dashed #a1a1aa",
        borderRadius: "8px",
        marginBottom: "1.5rem",
      }}
    >
      <h2>Upload a spreadsheet</h2>
      <p>Supported formats: CSV and Excel (.xlsx). Each sheet becomes a queryable table.</p>
      <div style={{ display: "flex", gap: "1rem", alignItems: "center", marginTop: "0.75rem" }}>
        <label htmlFor="dataset-file-input">
          <span style={{ marginRight: "0.5rem" }}>Choose file:</span>
          <input
            id="dataset-file-input"
            type="file"
            accept=".csv,.xlsx"
            disabled={busy}
            onChange={handleFileChange}
          />
        </label>
        <button type="button" onClick={onLoadSample} disabled={busy}>
          {busy ? "Loading…" : "Try sample dataset (Retail Sales)"}
        </button>
      </div>
    </section>
  );
}
