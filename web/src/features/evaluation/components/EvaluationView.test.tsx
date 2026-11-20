import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";
import type { EvalRunDetail } from "../types/eval";
import { EvaluationView } from "./EvaluationView";

const api = vi.hoisted(() => ({
  listEvalSets: vi.fn(),
  startEvalRun: vi.fn(),
  getEvalRun: vi.fn(),
}));
vi.mock("../api/eval-api", () => api);
// NumberFlow's web component cannot update inside jsdom; render the plain value instead.
vi.mock("@number-flow/react", () => ({
  default: ({ value, suffix = "" }: { value: number; suffix?: string }) => (
    <span>
      {value}
      {suffix}
    </span>
  ),
}));

const running: EvalRunDetail = {
  id: "00000000-0000-4000-8000-000000000001",
  set_name: "retail_sales",
  prompt_version: "v1",
  model: "ollama:llama3.2",
  started_at: "2026-11-20T00:00:00Z",
  finished_at: null,
  status: "running",
  error: null,
  total_questions: 2,
  correct_count: 0,
  rejected_count: 0,
  accuracy: 0,
  rejection_rate: 0,
  p50_latency_ms: 0,
  p95_latency_ms: 0,
  total_tokens_in: 0,
  total_tokens_out: 0,
  failure_categories: {},
  accuracy_by_path: {},
  results: [],
};

const result = {
  question_id: "rs-01",
  question: "How many orders?",
  category: "aggregate",
  difficulty: "easy",
  outcome: "correct" as const,
  generated_sql: "SELECT COUNT(*) FROM retail_sales",
  latency_ms: 120,
  tokens_in: 100,
  tokens_out: 20,
  failure_category: null,
  plan_skipped: false,
};

describe("EvaluationView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    api.listEvalSets.mockResolvedValue([
      {
        name: "retail_sales",
        demo_schema: "demo_retail_sales",
        description: "d",
        question_count: 2,
      },
    ]);
  });

  it("has no axe violations", async () => {
    const { container } = render(<EvaluationView pollIntervalMs={5} />);
    await screen.findByRole("option", { name: /retail_sales/i });

    expect(await axe(container)).toHaveNoViolations();
  });

  it("starts a run, shows progress, and polls until it completes", async () => {
    api.startEvalRun.mockResolvedValue(running);
    api.getEvalRun.mockResolvedValueOnce({ ...running, results: [result] }).mockResolvedValue({
      ...running,
      status: "completed",
      finished_at: "2026-11-20T00:01:00Z",
      correct_count: 2,
      accuracy: 1,
      accuracy_by_path: { planned: 1 },
      results: [result, { ...result, question_id: "rs-02" }],
    });
    render(<EvaluationView pollIntervalMs={5} />);
    await screen.findByRole("option", { name: /retail_sales/i });

    await userEvent.click(screen.getByRole("button", { name: /run evaluation/i }));

    expect(await screen.findByRole("status")).toHaveTextContent(/answered \d of 2/i);
    expect(await screen.findByText("rs-02")).toBeInTheDocument();
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    expect(api.getEvalRun).toHaveBeenCalledWith(running.id);
  });

  it("shows an alert when the run fails", async () => {
    api.startEvalRun.mockResolvedValue(running);
    api.getEvalRun.mockResolvedValue({
      ...running,
      status: "failed",
      error: "Evaluation failed (RuntimeError).",
    });
    render(<EvaluationView pollIntervalMs={5} />);
    await screen.findByRole("option", { name: /retail_sales/i });

    await userEvent.click(screen.getByRole("button", { name: /run evaluation/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Evaluation failed (RuntimeError).");
  });
});
