"use client";

import { ChevronDown, Table2 } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
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
    <Card aria-label={`Schema for ${table.table_name}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <div className="flex items-center gap-2.5">
          <span className="flex size-8 items-center justify-center rounded-lg bg-secondary text-foreground">
            <Table2 className="size-4" />
          </span>
          <div>
            <CardTitle className="font-mono">{table.table_name}</CardTitle>
            <CardDescription className="mt-0.5">
              {table.row_count.toLocaleString()} rows · {table.columns.length} columns
            </CardDescription>
          </div>
        </div>
        <Badge variant="success">Ready</Badge>
      </CardHeader>

      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Original</TableHead>
              <TableHead>Column Name</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Nullable</TableHead>
              <TableHead>Samples</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {table.columns.map((col) => (
              <TableRow key={col.id}>
                <TableCell className="text-muted-foreground">{col.original_name}</TableCell>
                <TableCell>
                  <Input
                    id={`col-name-${col.id}`}
                    name={`col_name_${col.id}`}
                    className="h-8 max-w-[200px] font-mono text-xs"
                    aria-label={`Column name for ${col.original_name}`}
                    value={draftNames[col.id] ?? col.column_name}
                    onChange={(e) =>
                      setDraftNames((prev) => ({ ...prev, [col.id]: e.target.value }))
                    }
                    onBlur={() => handleNameBlur(col)}
                  />
                </TableCell>
                <TableCell>
                  <select
                    id={`col-type-${col.id}`}
                    name={`col_type_${col.id}`}
                    className="h-8 rounded-md border border-input bg-card px-2.5 font-mono text-xs text-foreground shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
                </TableCell>
                <TableCell>
                  <Badge variant={col.nullable ? "secondary" : "outline"}>
                    {col.nullable ? "Yes" : "No"}
                  </Badge>
                </TableCell>
                <TableCell className="max-w-[240px] truncate font-mono text-xs text-muted-foreground">
                  {col.sample_values.slice(0, 3).map(String).join(", ")}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {table.preview_rows.length > 0 && (
          <details className="group border-t border-border px-5 py-3">
            <summary className="flex cursor-pointer list-none items-center gap-1.5 text-xs font-medium text-primary hover:underline">
              <ChevronDown className="size-3.5 transition-transform group-open:rotate-180" />
              Preview first {table.preview_rows.length} rows
            </summary>
            <div className="mt-3 overflow-hidden rounded-lg border border-border">
              <Table>
                <TableHeader>
                  <TableRow>
                    {table.columns.map((col) => (
                      <TableHead key={col.id} className="font-mono">
                        {col.column_name}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {table.preview_rows.map((row, idx) => (
                    <TableRow key={idx}>
                      {table.columns.map((col) => (
                        <TableCell key={col.id} className="font-mono text-xs">
                          {String(row[col.column_name] ?? "")}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </details>
        )}
      </CardContent>
    </Card>
  );
}
