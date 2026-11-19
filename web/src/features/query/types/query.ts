import { z } from "zod";

export const queryPlanSchema = z.object({
  intent: z.string(),
  tables: z.array(z.string()),
  columns: z.array(z.string()),
  aggregations: z.array(z.string()),
  filters: z.array(z.string()),
  needs_clarification: z.boolean(),
  clarifying_question: z.string().nullable().optional(),
  clarification_options: z.array(z.string()),
});

export const queryResponseSchema = z.object({
  id: z.string().uuid(),
  dataset_id: z.string().uuid(),
  question: z.string(),
  status: z.string(),
  plan: queryPlanSchema.nullable().optional(),
  generated_sql: z.string().nullable().optional(),
  columns: z.array(z.string()),
  rows: z.array(z.record(z.unknown())),
  row_count: z.number().int(),
  truncated: z.boolean(),
  rejection_reasons: z.array(z.object({ rule: z.string(), message: z.string() })),
  stage_timings_ms: z.record(z.number().int()),
  created_at: z.string(),
});

export type QueryPlan = z.infer<typeof queryPlanSchema>;
export type QueryResult = z.infer<typeof queryResponseSchema>;
