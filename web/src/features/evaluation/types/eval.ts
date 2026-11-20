import { z } from "zod";

export const goldenSetSummarySchema = z.object({
  name: z.string(),
  demo_schema: z.string(),
  description: z.string(),
  question_count: z.number().int(),
});

export const evalQuestionResultSchema = z.object({
  question_id: z.string(),
  question: z.string(),
  category: z.string(),
  difficulty: z.string(),
  outcome: z.enum(["correct", "wrong", "rejected", "error"]),
  generated_sql: z.string().nullable(),
  latency_ms: z.number().int(),
  tokens_in: z.number().int(),
  tokens_out: z.number().int(),
  failure_category: z.string().nullable(),
});

export const evalRunDetailSchema = z.object({
  id: z.string().uuid(),
  set_name: z.string(),
  prompt_version: z.string(),
  model: z.string(),
  started_at: z.string(),
  finished_at: z.string(),
  total_questions: z.number().int(),
  correct_count: z.number().int(),
  rejected_count: z.number().int(),
  accuracy: z.number(),
  rejection_rate: z.number(),
  p50_latency_ms: z.number().int(),
  p95_latency_ms: z.number().int(),
  total_tokens_in: z.number().int(),
  total_tokens_out: z.number().int(),
  failure_categories: z.record(z.string(), z.number().int()),
  results: z.array(evalQuestionResultSchema),
});

export type GoldenSetSummary = z.infer<typeof goldenSetSummarySchema>;
export type EvalRunDetail = z.infer<typeof evalRunDetailSchema>;
