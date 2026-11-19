"use client";

import { useState } from "react";
import { ALLOWED_PG_TYPES, type ColumnInfo, type TableInfo } from "../types/dataset";

interface SchemaReviewTableProps {
  table: TableInfo;
  onUpdateColumn: (columnId: string, payload: { column_name?: string; pg_type?: string }) => void;
}

export function SchemaReviewTable({ table, onUpdateColumn }: SchemaReviewTableProps) {
  const [draftNames, setDraftNames] = useState<Record<string, string>>({});

  function handleNameBlur(col: ColumnInfo) {
    const draft = draftNames[col.id]?.trim();
    if (draft && draft !== col.column_name) {
      onUpdateColumn(col.id, { column_name: draft });
    }
  }

  return (
    <section aria-label={`Schema for ${table.table_name}`} style={{ marginBottom: "2rem" }}>
      <h3>
        Table: <code>{table.table_name}</code> ({table.row_count} rows)
      </h3>
      <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: "1rem" }}>
        <thead>
          <tr>
            <th align="left">Original</th>
            <th align="left">Column Name</th>
            <th align="left">Type</th>
            <th align="left">Nullable</th>
            <th align="left">Samples</th>
          </tr>
        </thead>
        <tbody>
          {table.columns.map((col) => (
            <tr key={col.id} style={{ borderTop: "1px solid #e4e4e7" }}>
              <td>{col.original_name}</td>
              <td>
                <input
                  aria-label={`Column name for ${col.original_name}`}
                  value={draftNames[col.id] ?? col.column_name}
                  onChange={(e) => setDraftNames((prev) => ({ ...prev, [col.id]: e.target.value }))}
                  onBlur={() => handleNameBlur(col)}
                />
              </td>
              <td>
                <select
                  aria-label={`Type for ${col.column_name}`}
                  value={col.pg_type}
                  onChange={(e) => onUpdateColumn(col.id, { pg_type: e.target.value })}
                >
                  {ALLOWED_PG_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </td>
              <td>{col.nullable ? "Yes" : "No"}</td>
              <td>{col.sample_values.slice(0, 3).map(String).join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {table.preview_rows.length > 0 && (
        <details open>
          <summary>Preview (first {table.preview_rows.length} rows)</summary>
          <div style={{ overflowX: "auto", marginTop: "0.5rem" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr>
                  {table.columns.map((col) => (
                    <th key={col.id} align="left">
                      {col.column_name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.preview_rows.map((row, idx) => (
                  <tr key={idx} style={{ borderTop: "1px solid #e4e4e7" }}>
                    {table.columns.map((col) => (
                      <td key={col.id}>{String(row[col.column_name] ?? "")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </section>
  );
}
