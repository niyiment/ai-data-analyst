import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";
import { InsightsAndReportActions } from "./InsightsAndReportActions";
import { ReportsView } from "./ReportsView";

vi.mock("../api/report-api", () => ({
  generateInsights: vi.fn(),
  createReport: vi.fn(),
}));

describe("reports accessibility", () => {
  it("ReportsView with reports has no axe violations", async () => {
    const { container } = render(
      <ReportsView
        reports={[
          {
            id: "00000000-0000-4000-8000-000000000001",
            title: "Revenue by region",
            created_at: "2026-11-20T00:00:00Z",
          },
        ]}
        onGoToAnalyst={vi.fn()}
      />,
    );

    expect(screen.getByText("Revenue by region")).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("ReportsView empty state has no axe violations", async () => {
    const { container } = render(<ReportsView reports={[]} onGoToAnalyst={vi.fn()} />);

    expect(await axe(container)).toHaveNoViolations();
  });

  it("InsightsAndReportActions exposes named buttons", async () => {
    const { container } = render(
      <InsightsAndReportActions
        queryRunId="00000000-0000-4000-8000-000000000002"
        question="Revenue by region"
      />,
    );

    for (const button of screen.getAllByRole("button")) {
      expect(button).toHaveAccessibleName();
    }
    expect(await axe(container)).toHaveNoViolations();
  });
});
