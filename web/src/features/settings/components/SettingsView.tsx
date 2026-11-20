"use client";

import { RotateCcw, Save, Shield } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  DEFAULT_MODELS,
  clearLlmConfig,
  loadLlmConfig,
  saveLlmConfig,
  type LlmProvider,
} from "@/lib/llm-config";

const PROVIDER_LABELS: Record<LlmProvider, string> = {
  ollama: "Ollama (Free local)",
  ollama_cloud: "Ollama Cloud",
  gemini: "Google Gemini",
  claude: "Anthropic Claude",
};

const KEY_PLACEHOLDERS: Record<LlmProvider, string> = {
  ollama: "",
  ollama_cloud: "Ollama Cloud API key...",
  gemini: "AIza...",
  claude: "sk-ant-api03-...",
};

export function SettingsView() {
  const [provider, setProvider] = useState<LlmProvider>("ollama");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");

  useEffect(() => {
    const cfg = loadLlmConfig();
    setProvider(cfg.provider);
    setApiKey(cfg.apiKey);
    setModel(cfg.model);
  }, []);

  function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    saveLlmConfig({ provider, apiKey: apiKey.trim(), model: model.trim() });
    toast.success(`Saved: using ${PROVIDER_LABELS[provider]} for AI Analyst and Insights.`);
  }

  function handleClear() {
    clearLlmConfig();
    setProvider("ollama");
    setApiKey("");
    setModel("");
    toast.info("Reset to default: Ollama (free local model).");
  }

  return (
    <section aria-label="AI API Configuration" className="space-y-6">
      <div>
        <p className="text-xs font-medium uppercase tracking-wider text-primary">
          Workspace settings
        </p>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">AI API Configuration</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Uses Ollama (free local model) by default. Switch to Google Gemini, Anthropic Claude, or
          Ollama Cloud anytime.
        </p>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Provider &amp; credentials</CardTitle>
          <CardDescription>
            Keys are stored only in this browser tab&apos;s sessionStorage and sent per request.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="space-y-5" onSubmit={handleSave}>
            <div className="space-y-1.5">
              <label htmlFor="llm-provider-select" className="text-xs font-medium text-foreground">
                AI Provider
              </label>
              <select
                id="llm-provider-select"
                name="llmProvider"
                className="flex h-9 w-full rounded-md border border-input bg-card px-3 text-sm text-foreground shadow-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                value={provider}
                onChange={(e) => setProvider(e.target.value as LlmProvider)}
              >
                <option value="ollama">Ollama — Free local model (default, no API key)</option>
                <option value="ollama_cloud">Ollama Cloud — API key required</option>
                <option value="gemini">Google Gemini (gemini-2.5-flash)</option>
                <option value="claude">Anthropic Claude (claude-3-5-sonnet-latest)</option>
              </select>
            </div>

            {provider !== "ollama" && (
              <div className="space-y-1.5">
                <label
                  htmlFor="llm-api-key-input"
                  className="text-xs font-medium text-foreground"
                >
                  API Key (optional — leave blank to use server default)
                </label>
                <Input
                  id="llm-api-key-input"
                  name="llmApiKey"
                  type="password"
                  autoComplete="off"
                  placeholder={KEY_PLACEHOLDERS[provider]}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
                <p className="flex items-center gap-1.5 text-[11px] text-muted-foreground">
                  <Shield className="size-3 shrink-0" />
                  Never persisted to disk or logged on the server.
                </p>
              </div>
            )}

            <div className="space-y-1.5">
              <label htmlFor="llm-model-input" className="text-xs font-medium text-foreground">
                Model override (optional)
              </label>
              <Input
                id="llm-model-input"
                name="llmModel"
                type="text"
                className="font-mono"
                placeholder={DEFAULT_MODELS[provider]}
                value={model}
                onChange={(e) => setModel(e.target.value)}
              />
            </div>

            <div className="flex flex-wrap gap-2 pt-2">
              <Button type="submit">
                <Save className="size-4" />
                Save configuration
              </Button>
              <Button type="button" variant="outline" onClick={handleClear}>
                <RotateCcw className="size-4" />
                Reset to Ollama default
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </section>
  );
}
