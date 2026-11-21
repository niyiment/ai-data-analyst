"use client";

import { Clock, Download, FileText, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { ReportSummary } from "../api/report-api";

interface ReportsViewProps {
  reports: ReportSummary[];
  onGoToAnalyst: () => void;
}

export function ReportsView({ reports, onGoToAnalyst }: ReportsViewProps) {
  return (
    <section aria-label="Reports" className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-primary">
            Your generated insights
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Reports</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Review and export your pinned analytical reports as PDF or HTML.
          </p>
        </div>
        <Button type="button" onClick={onGoToAnalyst}>
          <Sparkles className="size-4" />
          New analysis
        </Button>
      </div>

      {reports.length > 0 && (
        <div className="space-y-3">
          {reports.map((report) => (
            <Card key={report.id}>
              <CardContent className="flex flex-col justify-between gap-4 p-5 sm:flex-row sm:items-center">
                <div className="space-y-1">
                  <h2 className="text-sm font-semibold text-foreground">{report.title}</h2>
                  <p className="text-xs text-muted-foreground">
                    Pinned query run with validated SQL, results, and insights.
                  </p>
                  <div className="flex items-center gap-1.5 pt-1 text-[11px] text-muted-foreground">
                    <Clock className="size-3" />
                    <span>{new Date(report.created_at).toLocaleString()}</span>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Button variant="outline" size="sm" asChild>
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
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12 text-center">
          <div className="mb-3 flex size-11 items-center justify-center rounded-xl bg-muted text-muted-foreground">
            <FileText className="size-5" />
          </div>
          <h2 className="text-sm font-semibold">
            {reports.length === 0 ? "No reports pinned yet" : "Reports that tell the whole story"}
          </h2>
          <p className="mt-1 max-w-md text-xs text-muted-foreground">
            Ask a question in AI Analyst and click &ldquo;Pin to report&rdquo; to export as PDF or
            HTML.
          </p>
        </CardContent>
      </Card>
    </section>
  );
}
