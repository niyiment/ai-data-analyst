import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { InsightsAndReportActions } from "./InsightsAndReportActions";

const api = vi.hoisted(() => ({ generateInsights: vi.fn(), createReport: vi.fn() }));
vi.mock("../api/report-api", () => api);
const toast = vi.hoisted(() => ({ success: vi.fn(), error: vi.fn() }));
vi.mock("sonner", () => ({ toast }));

const RUN_ID = "00000000-0000-4000-8000-000000000002";
const REPORT = { id: "00000000-0000-4000-8000-000000000009", title: "Q", created_at: "now" };

function renderActions(onReportCreated = vi.fn()) {
  render(
    <InsightsAndReportActions
      queryRunId={RUN_ID}
      question="Revenue by region"
      onReportCreated={onReportCreated}
    />,
  );
  return onReportCreated;
}

describe("InsightsAndReportActions", () => {
  beforeEach(() => vi.clearAllMocks());

  it("generates insights on demand and shows them in a labelled region", async () => {
    api.generateInsights.mockResolvedValue({
      summary: "North leads.",
      key_findings: ["North is 2x South"],
      next_questions: [],
    });
    renderActions();

    await userEvent.click(screen.getByRole("button", { name: /generate insights/i }));

    const region = await screen.findByRole("region", { name: /insights/i });
    expect(region).toHaveTextContent("North leads.");
    expect(region).toHaveTextContent("North is 2x South");
    expect(api.generateInsights).toHaveBeenCalledWith(RUN_ID);
  });

  it("pins the answer to a report and offers HTML and PDF downloads", async () => {
    api.createReport.mockResolvedValue(REPORT);
    const onReportCreated = renderActions();

    await userEvent.click(screen.getByRole("button", { name: /pin to report/i }));

    expect(await screen.findByRole("link", { name: /pdf/i })).toHaveAttribute(
      "href",
      `/api/v1/reports/${REPORT.id}/export?format=pdf`,
    );
    expect(screen.getByRole("link", { name: /html/i })).toHaveAttribute(
      "href",
      `/api/v1/reports/${REPORT.id}/export?format=html`,
    );
    expect(api.createReport).toHaveBeenCalledWith("Revenue by region", RUN_ID);
    expect(onReportCreated).toHaveBeenCalledWith(REPORT);
  });

  it("shows the server's error and re-enables the buttons when a call fails", async () => {
    api.generateInsights.mockRejectedValue(new Error("Global LLM quota exceeded."));
    renderActions();

    await userEvent.click(screen.getByRole("button", { name: /generate insights/i }));

    expect(toast.error).toHaveBeenCalledWith("Global LLM quota exceeded.");
    expect(screen.getByRole("button", { name: /generate insights/i })).toBeEnabled();
    expect(screen.queryByRole("region", { name: /insights/i })).not.toBeInTheDocument();
  });
});
