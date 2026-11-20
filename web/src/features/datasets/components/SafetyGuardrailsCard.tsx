"use client";

import { Clock, Lock, ShieldCheck } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const GUARDRAILS = [
  {
    title: "SQLGlot AST Validator",
    desc: "Single SELECT only, function & table allowlists",
    icon: ShieldCheck,
    tone: "bg-accent text-primary",
  },
  {
    title: "Read-only execution",
    desc: "Dedicated PostgreSQL role with row & time limits",
    icon: Lock,
    tone: "bg-emerald-50 text-emerald-700",
  },
  {
    title: "24-hour auto-deletion",
    desc: "Isolated per-dataset schema dropped automatically",
    icon: Clock,
    tone: "bg-secondary text-foreground",
  },
];

export function SafetyGuardrailsCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Safety &amp; privacy</CardTitle>
        <CardDescription>Built-in guardrails for every query</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {GUARDRAILS.map(({ title, desc, icon: Icon, tone }) => (
          <div key={title} className="flex items-start gap-3">
            <span className={`mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md ${tone}`}>
              <Icon className="size-4" />
            </span>
            <div className="text-xs leading-relaxed text-muted-foreground">
              <div className="font-medium text-foreground">{title}</div>
              {desc}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
