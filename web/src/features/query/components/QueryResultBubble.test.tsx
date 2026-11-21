import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";
import type { QueryResult } from "../types/query";
import { QueryResultBubble } from "./QueryResultBubble";

vi.mock("echarts", () => ({
  init: () => ({ setOption: vi.fn(), dispose: vi.fn() }),
}));

const base: QueryResult = {
  id: "00000000-0000-4000-8000-000000000001",
  dataset_id: "00000000-0000-4000-8000-000000000002",
  question: "Revenue by region",
  status: "succeeded",
  plan: null,
  generated_sql: "SELECT region, SUM(revenue) AS total FROM sales GROUP BY region",
  columns: ["region", "total"],
  rows: [
    { region: "North", total: 10 },
    { region: "South", total: 5 },
  ],
  row_count: 2,
  truncated: false,
  rejection_reasons: [],
  stage_timings_ms: {},
  chart_spec: null,
  created_at: "2026-11-20T00:00:00Z",
};

function renderBubble(result: QueryResult) {
  return render(<QueryResultBubble result={result} busy={false} onClarify={vi.fn()} />);
}

describe("QueryResultBubble charts", () => {
  it("renders the recommended chart as a labelled figure next to the table", async () => {
    const { container } = renderBubble({
      ...base,
      chart_spec: { chart_type: "bar", x: "region", y: "total", title: "Revenue by region" },
    });

    expect(screen.getByRole("figure", { name: /revenue by region/i })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /bar chart.*data in the table/i })).toBeInTheDocument();
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("shows only the table when there is no chart", () => {
    renderBubble(base);

    expect(screen.queryByRole("figure")).not.toBeInTheDocument();
    expect(screen.getByRole("table")).toBeInTheDocument();
  });
});

describe("QueryResultBubble states", () => {
  it("offers clarification options as buttons that resend the question", async () => {
    const onClarify = vi.fn();
    render(
      <QueryResultBubble
        busy={false}
        onClarify={onClarify}
        result={{
          ...base,
          status: "needs_clarification",
          plan: {
            intent: "rank products",
            tables: [],
            columns: [],
            aggregations: [],
            filters: [],
            needs_clarification: true,
            clarifying_question: "Rank by revenue or units?",
            clarification_options: ["By revenue", "By units"],
          },
        }}
      />,
    );

    expect(screen.getByText(/rank by revenue or units\?/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "By units" }));
    expect(onClarify).toHaveBeenCalledWith("Revenue by region", "By units");
  });

  it("announces validator rejections with each rule and reason", () => {
    renderBubble({
      ...base,
      status: "rejected",
      rejection_reasons: [{ rule: "single_select", message: "Only SELECT is allowed." }],
    });

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("single_select");
    expect(alert).toHaveTextContent("Only SELECT is allowed.");
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("copies the generated SQL to the clipboard", async () => {
    const user = userEvent.setup();
    const writeText = vi.spyOn(navigator.clipboard, "writeText").mockResolvedValue();
    renderBubble(base);

    await user.click(screen.getByRole("button", { name: /copy sql/i }));

    expect(writeText).toHaveBeenCalledWith(base.generated_sql);
  });
});
