"use client";

import * as echarts from "echarts";
import { useEffect, useId, useRef } from "react";
import { buildEChartsOption } from "../lib/echarts-mapper";
import type { ChartSpec } from "../types/chart";

interface ChartRendererProps {
  spec: ChartSpec | null;
  rows: Record<string, unknown>[];
}

export function ChartRenderer({ spec, rows }: ChartRendererProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const captionId = useId();
  const option = spec ? buildEChartsOption(spec, rows) : null;

  useEffect(() => {
    const el = containerRef.current;
    if (!el || !option) return;
    const chart = echarts.init(el);
    chart.setOption(option);
    return () => {
      chart.dispose();
    };
  }, [option]);

  if (!spec || !option) {
    return null;
  }

  return (
    <figure aria-labelledby={captionId} className="rounded-lg border border-border p-3">
      <figcaption id={captionId} className="mb-2 text-xs font-medium text-foreground">
        {spec.title}
      </figcaption>
      <div
        ref={containerRef}
        role="img"
        aria-label={`${spec.chart_type} chart of ${spec.y} by ${spec.x}; data in the table above`}
        style={{ width: "100%", height: "320px" }}
      />
    </figure>
  );
}
