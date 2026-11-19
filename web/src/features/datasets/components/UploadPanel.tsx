"use client";

import { useRef, useState, type ChangeEvent, type DragEvent } from "react";

interface UploadPanelProps {
  busy: boolean;
  onUploadFile: (file: File) => void;
  onLoadSample: () => void;
}

export function UploadPanel({ busy, onUploadFile, onLoadSample }: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragOver, setDragOver] = useState(false);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      onUploadFile(file);
      event.target.value = "";
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file && !busy) {
      onUploadFile(file);
    }
  }

  return (
    <section aria-label="Upload dataset">
      <div
        className={`upload-zone${dragOver ? " drag-over" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <div className="upload-icon" aria-hidden="true">
          <svg width="25" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7">
            <path d="M12 16V4m-5 5 5-5 5 5M4 16v4h16v-4" />
          </svg>
        </div>
        <h3>{busy ? "Uploading & inferring schema…" : "Drop your dataset here"}</h3>
        <p>Upload a CSV or Excel (.xlsx) file to create queryable tables in your session.</p>
        <button
          type="button"
          className="btn primary"
          disabled={busy}
          onClick={() => inputRef.current?.click()}
        >
          Choose file
        </button>
        <input
          ref={inputRef}
          id="dataset-file-input"
          type="file"
          accept=".csv,.xlsx"
          disabled={busy}
          onChange={handleFileChange}
          hidden
        />
        <small>Supported formats: CSV, XLSX · Maximum file size: 10 MB · Auto-deleted in 24h</small>
      </div>

      <div className="upload-lower">
        <div className="panel hint-card">
          <h3>Start with sample data</h3>
          <p>
            Explore the workspace immediately with our curated Retail Sales dataset. No file upload
            required.
          </p>
          <button
            type="button"
            className="btn"
            style={{ marginTop: "12px" }}
            disabled={busy}
            onClick={onLoadSample}
          >
            {busy ? "Loading…" : "Load Retail Sales sample →"}
          </button>
        </div>
        <div className="panel hint-card">
          <h3>What happens after upload?</h3>
          <p>
            We sanitise column names, infer PostgreSQL types, load each sheet into an isolated
            schema, and let you review or override types before querying.
          </p>
        </div>
      </div>
    </section>
  );
}
