import { z } from "zod";

export const sessionSchema = z.object({
  session_id: z.string().uuid(),
  created_at: z.string(),
  expires_at: z.string(),
  status: z.string(),
});

export const deleteSessionSchema = z.object({
  deleted: z.boolean(),
  schemas_dropped: z.number().int(),
});

export type SessionInfo = z.infer<typeof sessionSchema>;
export type DeleteSessionResult = z.infer<typeof deleteSessionSchema>;
