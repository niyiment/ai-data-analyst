import { describe, expect, it } from "vitest";
import type { ChartSpec } from "../types/chart";
import { buildEChartsOption } from "./echarts-mapper";

const rows = [
  { region: "North", total: "10.5" },
  { region: "South", total: 5 },
];
const spec = (chart_type: ChartSpec["chart_type"]): ChartSpec => ({
  chart_type,
  x: "region",
  y: "total",
  title: "Revenue",
});

describe("buildEChartsOption", () => {
  it.each(["bar", "line", "scatter"] as const)("maps %s charts to category/value axes", (type) => {
    const option = buildEChartsOption(spec(type), rows);

    expect(option).toMatchObject({
      title: { text: "Revenue" },
      xAxis: { type: "category", data: ["North", "South"] },
      yAxis: { type: "value" },
      series: [{ type, data: [10.5, 5] }],
    });
  });

  it("maps pie charts to name/value pairs", () => {
    const option = buildEChartsOption(spec("pie"), rows);

    expect(option).toMatchObject({
      series: [
        {
          type: "pie",
          data: [
            { name: "North", value: 10.5 },
            { name: "South", value: 5 },
          ],
        },
      ],
    });
  });

  it("returns null for no rows or columns missing from the result", () => {
    expect(buildEChartsOption(spec("bar"), [])).toBeNull();
    expect(buildEChartsOption({ ...spec("bar"), y: "missing" }, rows)).toBeNull();
  });
});
