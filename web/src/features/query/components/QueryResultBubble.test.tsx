import { render, screen } from "@testing-library/react";
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
