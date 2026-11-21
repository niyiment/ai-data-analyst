import { z } from "zod";
import { apiRequest } from "@/lib/api-client";

export const insightsSchema = z.object({
  summary: z.string(),
  key_findings: z.array(z.string()),
  next_questions: z.array(z.string()),
});

export const reportResponseSchema = z.object({
  id: z.string().uuid(),
  title: z.string(),
  created_at: z.string(),
});

export type InsightsData = z.infer<typeof insightsSchema>;
export type ReportSummary = z.infer<typeof reportResponseSchema>;

export function generateInsights(queryRunId: string): Promise<InsightsData> {
  return apiRequest(`/api/v1/queries/${queryRunId}/insights`, insightsSchema, {
    method: "POST",
  });
}

export function createReport(title: string, queryRunId: string): Promise<ReportSummary> {
  return apiRequest("/api/v1/reports", reportResponseSchema, {
    method: "POST",
    body: JSON.stringify({ title, items: [{ query_run_id: queryRunId }] }),
  });
}
