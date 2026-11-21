"use client";

import { AlertTriangle, Check, Copy, Sparkles } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ChartRenderer } from "@/features/charts";
import { InsightsAndReportActions, type ReportSummary } from "@/features/reports";
import type { QueryResult } from "../types/query";

interface QueryResultBubbleProps {
  result: QueryResult;
  busy: boolean;
  onClarify: (question: string, option: string) => void;
  onReportCreated?: (report: ReportSummary) => void;
}

export function QueryResultBubble({
  result,
  busy,
  onClarify,
  onReportCreated,
}: QueryResultBubbleProps) {
  const [copied, setCopied] = useState(false);

  async function handleCopySql(sql: string) {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      toast.success("SQL copied to clipboard");
      setTimeout(() => setCopied(false), 1800);
    } catch {
      toast.error("Could not copy SQL");
    }
  }

  if (result.status === "needs_clarification" && result.plan) {
    return (
      <div className="flex items-start gap-3">
        <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Sparkles className="size-3.5" />
        </span>
        <div className="flex-1 space-y-3 rounded-xl border border-border bg-secondary/50 p-4 text-sm">
          <p>
            <strong className="font-semibold">Clarification needed:</strong>{" "}
            {result.plan.clarifying_question}
          </p>
          <div className="flex flex-wrap gap-2">
            {result.plan.clarification_options.map((opt) => (
              <Button
                key={opt}
                type="button"
                variant="outline"
                size="sm"
                disabled={busy}
                onClick={() => onClarify(result.question, opt)}
              >
                {opt}
              </Button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (result.status === "rejected") {
    return (
      <div className="flex items-start gap-3">
        <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-red-50 text-destructive">
          <AlertTriangle className="size-3.5" />
        </span>
        <div
          role="alert"
          className="flex-1 space-y-2 rounded-xl border border-red-200 bg-red-50/60 p-4 text-sm text-red-900"
        >
          <p className="font-semibold">Query rejected by safety validator</p>
          <ul className="list-disc space-y-1 pl-5 text-xs">
            {result.rejection_reasons.map((r, i) => (
              <li key={i}>
                <code className="font-mono font-semibold">{r.rule}</code>: {r.message}
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3">
      <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
        <Sparkles className="size-3.5" />
      </span>
      <div className="min-w-0 flex-1 space-y-3 rounded-xl border border-border bg-card p-4 shadow-xs">
        {result.plan && (
          <p className="text-xs text-muted-foreground">
            <strong className="font-medium text-foreground">Plan:</strong> {result.plan.intent}
          </p>
        )}

        <div className="overflow-hidden rounded-lg border border-border">
          <div className="flex items-center justify-between border-b border-border bg-muted/40 px-3 py-2 text-xs">
            <span className="font-medium text-foreground">Query result</span>
            <Badge variant="default">
              {result.row_count} rows{result.truncated ? " (truncated)" : ""}
            </Badge>
          </div>
          <Table>
            <TableHeader>
              <TableRow>
                {result.columns.map((col) => (
                  <TableHead key={col} className="font-mono">
                    {col}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {result.rows.map((row, idx) => (
                <TableRow key={idx}>
                  {result.columns.map((col) => (
                    <TableCell key={col} className="font-mono text-xs">
                      {String(row[col] ?? "")}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        {result.chart_spec && <ChartRenderer spec={result.chart_spec} rows={result.rows} />}

        {result.generated_sql && (
          <div className="relative rounded-lg bg-slate-950 p-3 font-mono text-xs text-slate-100">
            <button
              type="button"
              onClick={() => void handleCopySql(result.generated_sql ?? "")}
              className="absolute top-2 right-2 inline-flex items-center gap-1 rounded-md bg-slate-800 px-2 py-1 text-[11px] text-slate-200 transition-colors hover:bg-slate-700 cursor-pointer"
              aria-label="Copy SQL"
            >
              {copied ? <Check className="size-3" /> : <Copy className="size-3" />}
              {copied ? "Copied" : "Copy"}
            </button>
            <pre className="overflow-x-auto pr-16 whitespace-pre-wrap">{result.generated_sql}</pre>
          </div>
        )}

        <InsightsAndReportActions
          queryRunId={result.id}
          question={result.question}
          onReportCreated={onReportCreated}
        />
      </div>
    </div>
  );
}
