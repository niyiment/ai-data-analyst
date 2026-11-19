import type { EChartsOption } from "echarts";
import type { ChartSpec } from "../types/chart";

export function buildEChartsOption(
  spec: ChartSpec,
  rows: Record<string, unknown>[],
): EChartsOption | null {
  if (rows.length === 0) return null;

  const first = rows[0];
  if (!first || !(spec.x in first) || !(spec.y in first)) {
    return null;
  }

  if (spec.chart_type === "pie") {
    return {
      title: { text: spec.title },
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: "60%",
          data: rows.map((r) => ({
            name: String(r[spec.x] ?? ""),
            value: Number(r[spec.y] ?? 0),
          })),
        },
      ],
    };
  }

  const xValues = rows.map((r) => String(r[spec.x] ?? ""));
  const yValues = rows.map((r) => Number(r[spec.y] ?? 0));

  return {
    title: { text: spec.title },
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: xValues },
    yAxis: { type: "value" },
    series: [{ type: spec.chart_type, data: yValues }],
  };
}
