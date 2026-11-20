import { z } from "zod";
import { apiRequest } from "@/lib/api-client";
import {
  evalRunDetailSchema,
  goldenSetSummarySchema,
  type EvalRunDetail,
  type GoldenSetSummary,
} from "../types/eval";

export function listEvalSets(): Promise<GoldenSetSummary[]> {
  return apiRequest("/api/v1/eval/sets", z.array(goldenSetSummarySchema));
}

export function startEvalRun(setName: string): Promise<EvalRunDetail> {
  return apiRequest("/api/v1/eval/runs", evalRunDetailSchema, {
    method: "POST",
    body: JSON.stringify({ set_name: setName }),
  });
}
