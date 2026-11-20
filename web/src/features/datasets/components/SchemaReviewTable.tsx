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
    <section className="panel" aria-label={`Schema for ${table.table_name}`} style={{ marginTop: "18px" }}>
      <div className="panel-head">
        <div>
          <div className="panel-title">Table: {table.table_name}</div>
          <div className="panel-sub">
            {table.row_count.toLocaleString()} rows · {table.columns.length} columns
          </div>
        </div>
        <span className="status">Ready</span>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Original</th>
              <th>Column Name</th>
              <th>Type</th>
              <th>Nullable</th>
              <th>Samples</th>
            </tr>
          </thead>
          <tbody>
            {table.columns.map((col) => (
              <tr key={col.id}>
                <td>{col.original_name}</td>
                <td>
                  <input
                    id={`col-name-${col.id}`}
                    name={`col_name_${col.id}`}
                    className="select"
                    aria-label={`Column name for ${col.original_name}`}
                    value={draftNames[col.id] ?? col.column_name}
                    onChange={(e) => setDraftNames((prev) => ({ ...prev, [col.id]: e.target.value }))}
                    onBlur={() => handleNameBlur(col)}
                  />
                </td>
                <td>
                  <select
                    id={`col-type-${col.id}`}
                    name={`col_type_${col.id}`}
                    className="select"
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
      </div>

      {table.preview_rows.length > 0 && (
        <details style={{ padding: "12px 18px 16px", borderTop: "1px solid #f0f2f6" }}>
          <summary style={{ cursor: "pointer", fontSize: "11px", fontWeight: 650, color: "#315eea" }}>
            Preview first {table.preview_rows.length} rows
          </summary>
          <div className="table-wrap" style={{ marginTop: "10px" }}>
            <table className="data-table">
              <thead>
                <tr>
                  {table.columns.map((col) => (
                    <th key={col.id}>{col.column_name}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.preview_rows.map((row, idx) => (
                  <tr key={idx}>
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
