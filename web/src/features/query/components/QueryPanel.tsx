"use client";

import {
  ArrowRight,
  Database,
  FileSpreadsheet,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  User,
} from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import type { ReportSummary } from "@/features/reports";
import { askQuestion } from "../api/query-api";
import type { QueryResult } from "../types/query";
import { QueryResultBubble } from "./QueryResultBubble";

const SUGGESTIONS = ["Show total rows per table", "Summarize top categories", "Compare by region"];

interface QueryPanelProps {
  datasetId: string;
  datasetName?: string;
  rowCount?: number;
  columnCount?: number;
  initialQuestion?: string | null;
  onInitialQuestionHandled?: () => void;
  onQueryCompleted?: () => void;
  onReportCreated?: (report: ReportSummary) => void;
  onViewSchema?: () => void;
}

export function QueryPanel({
  datasetId,
  datasetName = "Active dataset",
  rowCount = 0,
  columnCount = 0,
  initialQuestion,
  onInitialQuestionHandled,
  onQueryCompleted,
  onReportCreated,
  onViewSchema,
}: QueryPanelProps) {
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [history, setHistory] = useState<QueryResult[]>([]);

  async function runQuery(q: string, choice?: string) {
    setBusy(true);
    try {
      const res = await askQuestion(datasetId, q, choice);
      setHistory((prev) => [...prev, res]);
      onQueryCompleted?.();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Query failed.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (initialQuestion && initialQuestion.trim().length >= 2) {
      void runQuery(initialQuestion.trim());
      onInitialQuestionHandled?.();
    }
  }, [initialQuestion]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = question.trim();
    if (trimmed.length >= 2) {
      setQuestion("");
      void runQuery(trimmed);
    }
  }

  return (
    <section aria-label="AI Analyst" className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-primary">
            Natural language analytics
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">AI Analyst</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Ask questions about your dataset and inspect the validated read-only SQL.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => setHistory([])}>
            <RotateCcw className="size-3.5" />
            Clear conversation
          </Button>
          {onViewSchema && (
            <Button type="button" size="sm" onClick={onViewSchema}>
              <Database className="size-3.5" />
              View schema
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="flex flex-col overflow-hidden lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 border-b border-border py-3.5">
            <div>
              <CardTitle className="font-mono">{datasetName}</CardTitle>
              <CardDescription className="mt-0.5">
                Read-only SQL pipeline · AST validated
              </CardDescription>
            </div>
            <Badge variant="success">Connected</Badge>
          </CardHeader>

          <CardContent
            role="log"
            aria-label="Conversation"
            aria-busy={busy}
            className="flex-1 space-y-5 overflow-y-auto p-5"
          >
            <div className="flex items-start gap-3">
              <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Sparkles className="size-3.5" />
              </span>
              <div className="rounded-xl border border-border bg-secondary/50 px-4 py-3 text-sm">
                <p className="font-medium text-foreground">Welcome to AI Analyst.</p>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  Ask a question in plain English. I will generate a safe, read-only SQL query,
                  validate it, and return the results.
                </p>
              </div>
            </div>

            {history.map((item) => (
              <div key={item.id} className="space-y-4">
                <div className="flex items-start justify-end gap-3">
                  <div className="max-w-[85%] rounded-xl bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                    {item.question}
                  </div>
                  <span className="flex size-7 shrink-0 items-center justify-center rounded-full bg-secondary text-foreground">
                    <User className="size-3.5" />
                  </span>
                </div>
                <QueryResultBubble
                  result={item}
                  busy={busy}
                  onClarify={(q, opt) => void runQuery(q, opt)}
                  onReportCreated={onReportCreated}
                />
              </div>
            ))}
          </CardContent>

          <div className="border-t border-border bg-muted/30 p-4">
            <form className="flex gap-2" onSubmit={handleSubmit}>
              <Input
                id="question-input"
                type="text"
                placeholder="Ask a question about your data..."
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={busy}
                aria-label="Natural-language question"
              />
              <Button type="submit" disabled={busy || question.trim().length < 2}>
                {busy ? "Running…" : "Ask"}
                <ArrowRight className="size-4" />
              </Button>
            </form>
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setQuestion(s)}
                  className="rounded-full border border-border bg-card px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground cursor-pointer"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        </Card>

        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Analysis context</CardTitle>
            <CardDescription>Active dataset &amp; execution limits</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3 rounded-lg border border-border bg-secondary/40 p-3">
              <FileSpreadsheet className="size-5 shrink-0 text-primary" />
              <div className="min-w-0">
                <div className="truncate font-mono text-xs font-semibold">{datasetName}</div>
                <div className="text-[11px] text-muted-foreground">
                  {rowCount.toLocaleString()} rows · {columnCount} columns
                </div>
              </div>
            </div>

            <Separator />

            <dl className="space-y-2.5 text-xs">
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Rows indexed</dt>
                <dd className="font-mono font-medium tabular-nums">{rowCount.toLocaleString()}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Columns</dt>
                <dd className="font-mono font-medium tabular-nums">{columnCount}</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Row cap</dt>
                <dd className="font-mono font-medium">1,000 rows</dd>
              </div>
              <div className="flex items-center justify-between">
                <dt className="text-muted-foreground">Timeout</dt>
                <dd className="font-mono font-medium">10 seconds</dd>
              </div>
            </dl>

            <div className="flex items-start gap-2 rounded-lg bg-muted/60 p-3 text-[11px] leading-relaxed text-muted-foreground">
              <ShieldCheck className="mt-0.5 size-3.5 shrink-0 text-primary" />
              <span>
                AI-generated SQL is validated by SQLGlot before execution on a read-only PostgreSQL
                role.
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
