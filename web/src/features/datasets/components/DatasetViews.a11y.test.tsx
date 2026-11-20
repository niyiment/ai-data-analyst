import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { axe } from "vitest-axe";
import type { DatasetDetail, TableInfo } from "../types/dataset";
import { OverviewView } from "./OverviewView";
import { SafetyGuardrailsCard } from "./SafetyGuardrailsCard";
import { SchemaReviewTable } from "./SchemaReviewTable";
import { UploadPanel } from "./UploadPanel";

vi.mock("@number-flow/react", () => ({
  default: ({ value, suffix = "" }: { value: number; suffix?: string }) => (
    <span>
      {value}
      {suffix}
    </span>
  ),
}));

const table: TableInfo = {
  id: "00000000-0000-4000-8000-000000000010",
  table_name: "retail_sales",
  source_name: "Sheet1",
  row_count: 2,
  columns: [
    {
      id: "00000000-0000-4000-8000-000000000011",
      ordinal: 0,
      original_name: "Region",
      column_name: "region",
      pg_type: "text",
      nullable: false,
      sample_values: ["North", "South"],
    },
  ],
  preview_rows: [{ region: "North" }, { region: "South" }],
};

const dataset: DatasetDetail = {
  id: "00000000-0000-4000-8000-000000000001",
  original_filename: "sales.csv",
  file_type: "csv",
  size_bytes: 1024,
  status: "ready",
  created_at: "2026-11-20T00:00:00Z",
  expires_at: "2026-11-21T00:00:00Z",
  tables: [table],
};

function renderOverview(datasets: DatasetDetail[]) {
  return render(
    <OverviewView
      datasets={datasets}
      queryCount={3}
      reportCount={1}
      onNavigate={vi.fn()}
      onSelectDataset={vi.fn()}
      onQuickAsk={vi.fn()}
    />,
  );
}

describe("dataset views accessibility", () => {
  it("OverviewView with a dataset has no axe violations", async () => {
    const { container } = renderOverview([dataset]);

    expect(await axe(container)).toHaveNoViolations();
  });

  it("OverviewView without datasets has no axe violations", async () => {
    const { container } = renderOverview([]);

    expect(await axe(container)).toHaveNoViolations();
  });

  it("SchemaReviewTable labels every editable control", async () => {
    const { container } = render(<SchemaReviewTable table={table} onUpdateColumn={vi.fn()} />);

    expect(screen.getByRole("textbox", { name: /column name for region/i })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: /type for region/i })).toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("UploadPanel exposes its actions as buttons", async () => {
    const { container } = render(
      <UploadPanel busy={false} onUploadFile={vi.fn()} onLoadSample={vi.fn()} />,
    );

    expect(screen.getByRole("button", { name: /choose file/i })).toBeEnabled();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("SafetyGuardrailsCard has no axe violations", async () => {
    const { container } = render(<SafetyGuardrailsCard />);

    expect(await axe(container)).toHaveNoViolations();
  });
});
