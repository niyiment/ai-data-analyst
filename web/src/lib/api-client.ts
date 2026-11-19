import { z } from "zod";

export const apiErrorSchema = z.object({
  code: z.string(),
  message: z.string(),
  details: z.record(z.unknown()).nullable().optional(),
  request_id: z.string(),
});

export type ApiErrorPayload = z.infer<typeof apiErrorSchema>;

export class ApiClientError extends Error {
  readonly status: number;
  readonly payload: ApiErrorPayload | null;

  constructor(status: number, message: string, payload: ApiErrorPayload | null = null) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.payload = payload;
  }
}

export async function apiRequest<T>(
  path: string,
  schema: z.ZodType<T>,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(path, {
    credentials: "same-origin",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const raw: unknown = await response.json().catch(() => null);
    const parsed = apiErrorSchema.safeParse(raw);
    throw new ApiClientError(
      response.status,
      parsed.success ? parsed.data.message : `Request failed with status ${response.status}`,
      parsed.success ? parsed.data : null,
    );
  }

  const data: unknown = await response.json();
  return schema.parse(data);
}
