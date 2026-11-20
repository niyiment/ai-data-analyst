"use client";

import { ArrowRight, FileUp, Info, Sparkles } from "lucide-react";
import { useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface UploadPanelProps {
  busy: boolean;
  onUploadFile: (file: File) => void;
  onLoadSample: () => void;
}

export function UploadPanel({ busy, onUploadFile, onLoadSample }: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragOver, setDragOver] = useState(false);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      onUploadFile(file);
      event.target.value = "";
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragOver(false);
    const file = event.dataTransfer.files?.[0];
    if (file && !busy) {
      onUploadFile(file);
    }
  }

  return (
    <section aria-label="Upload dataset" className="space-y-4">
      <div
        className={cn(
          "flex flex-col items-center justify-center rounded-xl border-2 border-dashed bg-card px-6 py-12 text-center transition-colors",
          dragOver ? "border-primary bg-accent/50" : "border-border hover:border-primary/40",
        )}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
      >
        <div className="mb-3 flex size-12 items-center justify-center rounded-xl bg-accent text-primary">
          <FileUp className="size-6" />
        </div>
        <h3 className="text-base font-semibold">
          {busy ? "Uploading & inferring schema…" : "Drop your dataset here"}
        </h3>
        <p className="mt-1 max-w-md text-sm text-muted-foreground">
          Upload a CSV or Excel (.xlsx) file to create queryable tables in your session.
        </p>
        <Button
          type="button"
          className="mt-4"
          disabled={busy}
          onClick={() => inputRef.current?.click()}
        >
          Choose file
        </Button>
        <input
          ref={inputRef}
          id="dataset-file-input"
          type="file"
          accept=".csv,.xlsx"
          disabled={busy}
          onChange={handleFileChange}
          hidden
        />
        <p className="mt-3 text-xs text-muted-foreground">
          Supported formats: CSV, XLSX · Max size: 10 MB · Auto-deleted in 24h
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardContent className="flex h-full flex-col justify-between p-5">
            <div>
              <div className="flex items-center gap-2 text-sm font-semibold">
                <Sparkles className="size-4 text-primary" />
                Start with sample data
              </div>
              <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
                Explore the workspace immediately with our curated Retail Sales dataset. No file
                upload required.
              </p>
            </div>
            <div className="mt-4">
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={busy}
                onClick={onLoadSample}
              >
                {busy ? "Loading…" : "Load Retail Sales sample"}
                <ArrowRight className="size-3.5" />
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-5">
            <div className="flex items-center gap-2 text-sm font-semibold">
              <Info className="size-4 text-muted-foreground" />
              What happens after upload?
            </div>
            <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">
              We sanitise column names, infer PostgreSQL types, load each sheet into an isolated
              schema, and let you review or override types before querying.
            </p>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
