"use client";

import NumberFlow from "@number-flow/react";
import {
  ArrowRight,
  CheckCircle2,
  Database,
  FileSpreadsheet,
  FileText,
  Plus,
  Rows3,
  Sparkles,
} from "lucide-react";
import { useState, type FormEvent } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { DatasetDetail } from "../types/dataset";
import { SafetyGuardrailsCard } from "./SafetyGuardrailsCard";
import type { WorkspacePage } from "./WorkspaceShell";

interface OverviewViewProps {
  datasets: DatasetDetail[];
  queryCount: number;
  reportCount: number;
  onNavigate: (page: WorkspacePage) => void;
  onSelectDataset: (dataset: DatasetDetail) => void;
  onQuickAsk: (question: string) => void;
}

export function OverviewView({
  datasets,
  queryCount,
  reportCount,
  onNavigate,
  onSelectDataset,
  onQuickAsk,
}: OverviewViewProps) {
  const [quickQuestion, setQuickQuestion] = useState("");
  const totalRows = datasets.reduce(
    (sum, ds) => sum + ds.tables.reduce((tSum, t) => tSum + t.row_count, 0),
    0,
  );

  function handleQuickSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = quickQuestion.trim();
    if (trimmed.length >= 2) {
      onQuickAsk(trimmed);
      setQuickQuestion("");
    }
  }

  const metrics = [
    {
      label: "Datasets uploaded",
      value: datasets.length,
      foot: "Max 3 per anonymous session",
      icon: Database,
    },
    {
      label: "Questions answered",
      value: queryCount,
      foot: "Validated read-only SQL",
      icon: CheckCircle2,
    },
    {
      label: "Reports generated",
      value: reportCount,
      foot: "Exportable as PDF & HTML",
      icon: FileText,
    },
    {
      label: "Rows indexed",
      value: totalRows,
      foot: "Across active session tables",
      icon: Rows3,
    },
  ];

  return (
    <section aria-label="Workspace overview" className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-primary">
            Your analytics workspace
          </p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">Analytics Overview</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Upload spreadsheets, inspect inferred schemas, and run validated read-only SQL.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" onClick={() => onNavigate("datasets")}>
            <Plus className="size-4" />
            Upload dataset
          </Button>
          <Button type="button" onClick={() => onNavigate("analyst")}>
            <Sparkles className="size-4" />
            Ask your data
          </Button>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map(({ label, value, foot, icon: Icon }) => (
          <Card key={label}>
            <CardContent className="p-5">
              <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
                <span>{label}</span>
                <span className="flex size-8 items-center justify-center rounded-lg bg-secondary text-foreground">
                  <Icon className="size-4" />
                </span>
              </div>
              <div className="mt-3 text-2xl font-semibold tracking-tight tabular-nums">
                <NumberFlow value={value} />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">{foot}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
            <div>
              <CardTitle>Recent datasets</CardTitle>
              <CardDescription className="mt-1">
                Your uploaded files in this 24-hour session
              </CardDescription>
            </div>
            <Button type="button" variant="ghost" size="sm" onClick={() => onNavigate("datasets")}>
              Manage
              <ArrowRight className="size-3.5" />
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {datasets.length === 0 ? (
              <div className="px-5 py-10 text-center text-sm text-muted-foreground">
                No datasets uploaded yet. Upload a CSV/XLSX file or load a sample dataset to begin.
              </div>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Dataset</TableHead>
                    <TableHead>Tables</TableHead>
                    <TableHead>Rows</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {datasets.map((ds) => {
                    const rows = ds.tables.reduce((s, t) => s + t.row_count, 0);
                    return (
                      <TableRow
                        key={ds.id}
                        className="cursor-pointer"
                        onClick={() => {
                          onSelectDataset(ds);
                          onNavigate("analyst");
                        }}
                      >
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            <FileSpreadsheet className="size-4 text-primary" />
                            <span>{ds.original_filename}</span>
                          </div>
                        </TableCell>
                        <TableCell className="tabular-nums">{ds.tables.length}</TableCell>
                        <TableCell className="tabular-nums">{rows.toLocaleString()}</TableCell>
                        <TableCell>
                          <Badge variant="success">{ds.status}</Badge>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>

        <SafetyGuardrailsCard />
      </div>

      <Card className="border-primary/20 bg-card">
        <CardContent className="p-5">
          <form
            className="flex flex-col gap-4 md:flex-row md:items-center"
            onSubmit={handleQuickSubmit}
          >
            <div className="flex items-center gap-3 md:flex-1">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Sparkles className="size-5" />
              </div>
              <div>
                <div className="text-sm font-semibold">Have a question about your data?</div>
                <p className="text-xs text-muted-foreground">
                  Ask in plain English. Get validated SQL, tables, charts, and insights in seconds.
                </p>
              </div>
            </div>
            <div className="flex w-full gap-2 md:max-w-md">
              <Input
                id="quick-question-input"
                name="quickQuestion"
                type="text"
                value={quickQuestion}
                onChange={(e) => setQuickQuestion(e.target.value)}
                placeholder="e.g. Which region had the highest sales?"
                aria-label="Quick question"
              />
              <Button type="submit" aria-label="Ask">
                Ask
                <ArrowRight className="size-4" />
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </section>
  );
}
