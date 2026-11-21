import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { z } from "zod";
import { ApiClientError, apiRequest } from "./api-client";
import { saveLlmConfig } from "./llm-config";

const schema = z.object({ ok: z.boolean() });

function stubFetch(status: number, body: unknown, raw = false) {
  const fetchMock = vi.fn(
    async () =>
      new Response(raw ? (body as string) : JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("apiRequest", () => {
  beforeEach(() => window.sessionStorage.clear());
  afterEach(() => vi.unstubAllGlobals());

  it("returns schema-validated data and sends same-origin JSON requests", async () => {
    const fetchMock = stubFetch(200, { ok: true });

    await expect(apiRequest("/api/v1/x", schema)).resolves.toEqual({ ok: true });

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/api/v1/x");
    expect(init.credentials).toBe("same-origin");
    expect(init.headers).toMatchObject({ "Content-Type": "application/json" });
    expect(init.headers).not.toHaveProperty("X-LLM-Provider");
  });

  it("forwards the saved LLM provider, model, and key as headers", async () => {
    saveLlmConfig({ provider: "gemini", apiKey: " key-123 ", model: "gemini-2.5-pro" });
    const fetchMock = stubFetch(200, { ok: true });

    await apiRequest("/api/v1/x", schema);

    const init = (fetchMock.mock.calls[0] as unknown as [string, RequestInit])[1];
    expect(init.headers).toMatchObject({
      "X-LLM-Provider": "gemini",
      "X-LLM-Api-Key": "key-123",
      "X-LLM-Model": "gemini-2.5-pro",
    });
  });

  it("raises ApiClientError with the server's message and payload", async () => {
    stubFetch(429, {
      code: "RATE_LIMITED",
      message: "Rate limit exceeded. Retry in 30 seconds.",
      details: { retry_after_seconds: 30 },
      request_id: "r1",
    });

    const error = await apiRequest("/api/v1/x", schema).catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiClientError);
    expect((error as ApiClientError).status).toBe(429);
    expect((error as ApiClientError).message).toBe("Rate limit exceeded. Retry in 30 seconds.");
    expect((error as ApiClientError).payload?.code).toBe("RATE_LIMITED");
  });

  it("falls back to a generic message when the error body is not the standard shape", async () => {
    stubFetch(502, "<html>Bad gateway</html>", true);

    await expect(apiRequest("/api/v1/x", schema)).rejects.toThrow("Request failed with status 502");
  });

  it("rejects responses that do not match the schema", async () => {
    stubFetch(200, { ok: "yes" });

    await expect(apiRequest("/api/v1/x", schema)).rejects.toThrow();
  });
});
