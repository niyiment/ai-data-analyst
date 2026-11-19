"use client";

import * as echarts from "echarts";
import { useEffect, useRef } from "react";
import { buildEChartsOption } from "../lib/echarts-mapper";
import type { ChartSpec } from "../types/chart";

interface ChartRendererProps {
  spec: ChartSpec | null;
  rows: Record<string, unknown>[];
}

export function ChartRenderer({ spec, rows }: ChartRendererProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
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
    <figure style={{ margin: "1rem 0" }}>
      <div
        ref={containerRef}
        role="img"
        aria-label={`Chart: ${spec.title}`}
        style={{ width: "100%", height: "320px" }}
      />
    </figure>
  );
}
