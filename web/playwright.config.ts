import { defineConfig, devices } from "@playwright/test";

// Full-stack E2E: browser -> Next.js (same-origin /api proxy) -> FastAPI -> PostgreSQL.
// Only the LLM is replaced, by a deterministic Ollama-compatible stub.
// Prerequisites: `docker compose up -d postgres` and `alembic upgrade head`.
const WEB_PORT = 3100;
const API_PORT = 8001;
const STUB_PORT = 11500;
const isCI = Boolean(process.env.CI);

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: isCI ? 1 : 0,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: isCI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://localhost:${WEB_PORT}`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "node e2e/llm-stub.mjs",
      url: `http://127.0.0.1:${STUB_PORT}/health`,
      env: { LLM_STUB_PORT: String(STUB_PORT) },
      reuseExistingServer: !isCI,
    },
    {
      command: "uv run python -m app",
      cwd: "../api",
      url: `http://127.0.0.1:${API_PORT}/health`,
      timeout: 120_000,
      env: {
        API_PORT: String(API_PORT),
        LLM_PROVIDER: "ollama",
        OLLAMA_BASE_URL: `http://127.0.0.1:${STUB_PORT}`,
        OLLAMA_MODEL: "e2e-stub",
        QUESTIONS_PER_SESSION_PER_HOUR: "1000",
        LLM_DAILY_CALL_BUDGET: "100000",
      },
      reuseExistingServer: !isCI,
    },
    {
      command: `pnpm exec next dev --port ${WEB_PORT}`,
      url: `http://localhost:${WEB_PORT}`,
      timeout: 180_000,
      env: { API_BASE_URL: `http://127.0.0.1:${API_PORT}` },
      reuseExistingServer: !isCI,
    },
  ],
});
