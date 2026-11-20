import { apiRequest } from "@/lib/api-client";
import { queryResponseSchema, type QueryResult } from "../types/query";

export function askQuestion(
  datasetId: string,
  question: string,
  clarificationChoice?: string,
): Promise<QueryResult> {
  return apiRequest(`/api/v1/datasets/${datasetId}/queries`, queryResponseSchema, {
    method: "POST",
    body: JSON.stringify({
      question,
      clarification_choice: clarificationChoice ?? null,
    }),
  });
}
