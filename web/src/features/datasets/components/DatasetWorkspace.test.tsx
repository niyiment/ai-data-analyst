import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";
import { DatasetWorkspace } from "./DatasetWorkspace";

vi.mock("echarts", () => ({ init: () => ({ setOption: vi.fn(), dispose: vi.fn() }) }));
vi.mock("@number-flow/react", () => ({
  default: ({ value, suffix = "" }: { value: number; suffix?: string }) => (
    <span>
      {value}
      {suffix}
    </span>
  ),
}));

const DATASET_ID = "00000000-0000-4000-8000-0000000000d1";
const session = (id: string) => ({
  session_id: id,
  created_at: "2026-11-20T00:00:00Z",
  expires_at: "2026-11-21T00:00:00Z",
  status: "active",
});
const dataset = {
  id: DATASET_ID,
  original_filename: "retail_sales.csv",
  file_type: "csv",
  size_bytes: 512,
  status: "ready",
  created_at: "2026-11-20T00:00:00Z",
  expires_at: "2026-11-21T00:00:00Z",
  tables: [
    {
      id: "00000000-0000-4000-8000-0000000000a1",
      table_name: "retail_sales",
      source_name: "retail_sales.csv",
      row_count: 2,
      columns: [
        {
          id: "00000000-0000-4000-8000-0000000000c2",
          ordinal: 0,
          original_name: "region",
          column_name: "region",
          pg_type: "text",
          nullable: false,
          sample_values: ["North"],
        },
      ],
      preview_rows: [{ region: "North" }],
    },
  ],
};
const answer = {
  id: "00000000-0000-4000-8000-0000000000b1",
  dataset_id: DATASET_ID,
  question: "Revenue by region",
  status: "succeeded",
  plan: null,
  generated_sql: "SELECT region, SUM(revenue) AS total FROM retail_sales GROUP BY region",
  columns: ["region", "total"],
  rows: [
    { region: "North", total: 10 },
    { region: "South", total: 5 },
  ],
  row_count: 2,
  truncated: false,
  rejection_reasons: [],
  stage_timings_ms: { generate: 5 },
  chart_spec: { chart_type: "bar", x: "region", y: "total", title: "Revenue by region" },
  created_at: "2026-11-20T00:00:00Z",
};

type Route = { status?: number; body: unknown };
const routes: Record<string, Route> = {
  "GET /api/v1/sessions/me": {
    status: 401,
    body: { code: "SESSION_EXPIRED", message: "Session expired.", request_id: "r1" },
  },
  "POST /api/v1/sessions": { body: session("00000000-0000-4000-8000-0000000000e1") },
  "POST /api/v1/datasets/samples/retail_sales": { body: dataset },
  [`POST /api/v1/datasets/${DATASET_ID}/queries`]: { body: answer },
  "GET /api/v1/eval/sets": { body: [] },
  "DELETE /api/v1/sessions/me": { body: { deleted: true, schemas_dropped: 1 } },
};
const calls: string[] = [];

beforeEach(() => {
  calls.length = 0;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const key = `${init?.method ?? "GET"} ${url}`;
      calls.push(key);
      const route = routes[key];
      if (!route) return new Response(JSON.stringify({}), { status: 404 });
      return new Response(JSON.stringify(route.body), { status: route.status ?? 200 });
    }),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function nav(name: RegExp) {
  return within(screen.getByRole("navigation", { name: /workspace/i })).getByRole("button", {
    name,
  });
}

describe("DatasetWorkspace", () => {
  it("replaces an expired session, loads the sample, and answers with a table and chart", async () => {
    const { container } = render(<DatasetWorkspace />);
    expect(await screen.findByText(/auto-deletes/i)).toBeInTheDocument();
    expect(calls).toEqual(["GET /api/v1/sessions/me", "POST /api/v1/sessions"]);

    await userEvent.click(nav(/datasets/i));
    await userEvent.click(screen.getByRole("button", { name: /load retail sales sample/i }));
    expect(await screen.findByRole("textbox", { name: /column name for region/i })).toBeVisible();

    await userEvent.click(nav(/ai analyst/i));
    await userEvent.type(screen.getByRole("textbox", { name: /question/i }), "Revenue by region");
    await userEvent.click(screen.getByRole("button", { name: /^ask$/i }));

    expect(await screen.findByRole("figure", { name: /revenue by region/i })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "North" })).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("renders every page and deletes data into a fresh session", async () => {
    render(<DatasetWorkspace />);
    await screen.findByText(/auto-deletes/i);

    for (const page of [/reports/i, /evaluation/i, /overview/i]) {
      await userEvent.click(nav(page));
      expect(nav(page)).toHaveAttribute("aria-current", "page");
    }
    await userEvent.click(screen.getByRole("button", { name: /ai settings/i }));
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /delete my data/i }));
    await vi.waitFor(() => expect(calls).toContain("DELETE /api/v1/sessions/me"));
    await vi.waitFor(() =>
      expect(calls.filter((c) => c === "POST /api/v1/sessions")).toHaveLength(2),
    );
  });
});
