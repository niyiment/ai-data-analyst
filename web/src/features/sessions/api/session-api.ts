import { apiRequest } from "@/lib/api-client";
import {
  deleteSessionSchema,
  sessionSchema,
  type DeleteSessionResult,
  type SessionInfo,
} from "../types/session";

export function createSession(): Promise<SessionInfo> {
  return apiRequest("/api/v1/sessions", sessionSchema, { method: "POST" });
}

export function getMySession(): Promise<SessionInfo> {
  return apiRequest("/api/v1/sessions/me", sessionSchema, { method: "GET" });
}

export function deleteMySession(): Promise<DeleteSessionResult> {
  return apiRequest("/api/v1/sessions/me", deleteSessionSchema, { method: "DELETE" });
}
