"use client";

import NumberFlow from "@number-flow/react";
import { AlertCircle, CheckCircle2, Clock, Play, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { listEvalSets, startEvalRun } from "../api/eval-api";
import type { EvalRunDetail, GoldenSetSummary } from "../types/eval";

export function EvaluationView() {
  const [sets, setSets] = useState<GoldenSetSummary[]>([]);
  const [selectedSet, setSelectedSet] = useState("retail_sales");
  const [run, setRun] = useState<EvalRunDetail | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const loaded = await listEvalSets();
        setSets(loaded);
        if (loaded.length > 0 && loaded[0]) {
          setSelectedSet(loaded[0].name);
        }
      } catch (err) {
        toast.error(err instanceof Error ? err.message : "Could not load evaluation sets.");
      }
    })();
  }, []);

  async function handleRun() {
    setBusy(true);
    try {
      const result = await startEvalRun(selectedSet);
      setRun(result);
      toast.success(`Evaluation complete: ${Math.round(result.accuracy * 100)}% accuracy`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Evaluation run failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-label="Evaluation" className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-primary">
            Quality &amp; benchmarks
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Evaluation</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Run golden question sets to measure SQL accuracy, validator rejections, and latency.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label htmlFor="eval-set-select" className="sr-only">
            Golden question set
          </label>
          <select
            id="eval-set-select"
            name="evalSet"
            className="h-9 rounded-md border border-input bg-card px-3 text-sm text-foreground shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            value={selectedSet}
            onChange={(e) => setSelectedSet(e.target.value)}
            disabled={busy}
          >
            {sets.map((s) => (
              <option key={s.name} value={s.name}>
                {s.name} ({s.question_count} questions)
              </option>
            ))}
          </select>
          <Button type="button" disabled={busy} onClick={() => void handleRun()}>
            <Play className="size-3.5" />
            {busy ? "Running…" : "Run evaluation"}
          </Button>
        </div>
      </div>

      <div aria-live="polite" className="space-y-6">
        {run ? (
          <>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span>Execution accuracy</span>
                    <CheckCircle2 className="size-4 text-emerald-600" />
                  </div>
                  <div className="mt-3 text-2xl font-semibold tracking-tight tabular-nums">
                    <NumberFlow value={Math.round(run.accuracy * 100)} suffix="%" />
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {run.correct_count} of {run.total_questions} passed
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span>Rejection rate</span>
                    <AlertCircle className="size-4 text-amber-600" />
                  </div>
                  <div className="mt-3 text-2xl font-semibold tracking-tight tabular-nums">
                    <NumberFlow value={Math.round(run.rejection_rate * 100)} suffix="%" />
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {run.rejected_count} blocked by validator
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span>p95 latency</span>
                    <Clock className="size-4 text-muted-foreground" />
                  </div>
                  <div className="mt-3 text-2xl font-semibold tracking-tight tabular-nums">
                    <NumberFlow value={run.p95_latency_ms} suffix=" ms" />
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">p50: {run.p50_latency_ms} ms</p>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="p-5">
                  <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                    <span>Token usage</span>
                    <Sparkles className="size-4 text-primary" />
                  </div>
                  <div className="mt-3 text-2xl font-semibold tracking-tight tabular-nums">
                    <NumberFlow value={run.total_tokens_in + run.total_tokens_out} />
                  </div>
                  <p className="mt-1 truncate text-xs text-muted-foreground">Model: {run.model}</p>
                </CardContent>
              </Card>
            </div>

            <Card>
              <CardHeader>
                <CardTitle>Question results ({run.set_name})</CardTitle>
                <CardDescription>Prompt {run.prompt_version}</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Question</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Difficulty</TableHead>
                      <TableHead>Outcome</TableHead>
                      <TableHead>Latency</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {run.results.map((r) => (
                      <TableRow key={r.question_id}>
                        <TableCell className="font-mono text-xs">{r.question_id}</TableCell>
                        <TableCell>{r.question}</TableCell>
                        <TableCell>
                          <Badge variant="secondary">{r.category}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{r.difficulty}</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={r.outcome === "correct" ? "success" : "warning"}>
                            {r.outcome}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs tabular-nums">
                          {r.latency_ms} ms
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <div className="mb-3 flex size-11 items-center justify-center rounded-xl bg-muted text-muted-foreground">
                <CheckCircle2 className="size-5" />
              </div>
              <h2 className="text-sm font-semibold">Ready to benchmark</h2>
              <p className="mt-1 max-w-md text-xs text-muted-foreground">
                Select a golden set above and click &ldquo;Run evaluation&rdquo; to inspect accuracy
                and validator safety.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </section>
  );
}
