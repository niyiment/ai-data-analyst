"use client";

import { useEffect, useRef, useState } from "react";
import { getEvalRun, startEvalRun } from "../api/eval-api";
import type { EvalRunDetail } from "../types/eval";

const DEFAULT_POLL_MS = 1500;

/** Start an evaluation run and poll it until it is no longer running. */
export function useEvalRun(pollIntervalMs: number = DEFAULT_POLL_MS) {
  const [run, setRun] = useState<EvalRunDetail | null>(null);
  const [requestError, setRequestError] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!run || run.status !== "running") return;
    timer.current = setTimeout(() => {
      getEvalRun(run.id)
        .then(setRun)
        .catch((err: unknown) => {
          setRequestError(err instanceof Error ? err.message : "Could not load run progress.");
          setRun((prev) => (prev ? { ...prev, status: "failed" } : prev));
        });
    }, pollIntervalMs);
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, [run, pollIntervalMs]);

  async function start(setName: string) {
    setRequestError(null);
    try {
      setRun(await startEvalRun(setName));
    } catch (err) {
      setRequestError(err instanceof Error ? err.message : "Could not start the evaluation.");
    }
  }

  const running = run?.status === "running";
  const error = requestError ?? (run?.status === "failed" ? (run.error ?? "Run failed.") : null);
  return { run, running, error, start };
}
