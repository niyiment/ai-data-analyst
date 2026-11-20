"use client";

import { Download, Pin, Sparkles } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  createReport,
  generateInsights,
  type InsightsData,
  type ReportSummary,
} from "../api/report-api";

interface InsightsAndReportActionsProps {
  queryRunId: string;
  question: string;
  onReportCreated?: (report: ReportSummary) => void;
}

export function InsightsAndReportActions({
  queryRunId,
  question,
  onReportCreated,
}: InsightsAndReportActionsProps) {
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [report, setReport] = useState<ReportSummary | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleGenerateInsights() {
    setBusy(true);
    try {
      setInsights(await generateInsights(queryRunId));
      toast.success("AI insights generated");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not generate insights.");
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateReport() {
    setBusy(true);
    try {
      const created = await createReport(question, queryRunId);
      setReport(created);
      onReportCreated?.(created);
      toast.success("Pinned to reports");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not create report.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3 pt-1">
      <div className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={busy}
          onClick={() => void handleGenerateInsights()}
        >
          <Sparkles className="size-3.5 text-primary" />
          {busy ? "Working…" : "Generate insights"}
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={busy}
          onClick={() => void handleCreateReport()}
        >
          <Pin className="size-3.5" />
          Pin to report
        </Button>
        {report && (
          <>
            <Button size="sm" variant="secondary" asChild>
              <a href={`/api/v1/reports/${report.id}/export?format=html`} download>
                <Download className="size-3.5" />
                HTML
              </a>
            </Button>
            <Button size="sm" asChild>
              <a href={`/api/v1/reports/${report.id}/export?format=pdf`} download>
                <Download className="size-3.5" />
                PDF
              </a>
            </Button>
          </>
        )}
      </div>

      {insights && (
        <section
          aria-label="Insights"
          className="rounded-lg border border-primary/20 bg-accent/60 p-3.5 text-xs leading-relaxed"
        >
          <div className="mb-1.5 flex items-center gap-1.5 font-semibold text-primary">
            <Sparkles className="size-3.5" />
            AI Insights
          </div>
          <p className="text-foreground">{insights.summary}</p>
          {insights.key_findings.length > 0 && (
            <ul className="mt-2 list-disc space-y-1 pl-4 text-muted-foreground">
              {insights.key_findings.map((finding, idx) => (
                <li key={idx}>{finding}</li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}
