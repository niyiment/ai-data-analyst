import { z } from "zod";

export const ALLOWED_PG_TYPES = [
  "text",
  "bigint",
  "double precision",
  "boolean",
  "date",
  "timestamp",
] as const;

export const columnSchema = z.object({
  id: z.string().uuid(),
  ordinal: z.number().int(),
  original_name: z.string(),
  column_name: z.string(),
  pg_type: z.string(),
  nullable: z.boolean(),
  sample_values: z.array(z.unknown()),
  description: z.string().nullable().optional(),
});

export const tableSchema = z.object({
  id: z.string().uuid(),
  table_name: z.string(),
  source_name: z.string(),
  row_count: z.number().int(),
  columns: z.array(columnSchema),
  preview_rows: z.array(z.record(z.unknown())),
});

export const datasetDetailSchema = z.object({
  id: z.string().uuid(),
  original_filename: z.string(),
  file_type: z.string(),
  size_bytes: z.number().int(),
  status: z.string(),
  created_at: z.string(),
  expires_at: z.string(),
  tables: z.array(tableSchema),
});

export type ColumnInfo = z.infer<typeof columnSchema>;
export type TableInfo = z.infer<typeof tableSchema>;
export type DatasetDetail = z.infer<typeof datasetDetailSchema>;
