import { z } from "zod";

export const chartSpecSchema = z.object({
  chart_type: z.enum(["bar", "line", "pie", "scatter"]),
  x: z.string(),
  y: z.string(),
  series: z.string().nullable().optional(),
  title: z.string(),
});

export type ChartSpec = z.infer<typeof chartSpecSchema>;
