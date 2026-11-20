"use client";

import { useEffect, useState, type FormEvent } from "react";
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
  const [savedNotice, setSavedNotice] = useState<string | null>(null);

  useEffect(() => {
    const cfg = loadLlmConfig();
    setProvider(cfg.provider);
    setApiKey(cfg.apiKey);
    setModel(cfg.model);
  }, []);

  function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    saveLlmConfig({ provider, apiKey: apiKey.trim(), model: model.trim() });
    setSavedNotice(`Saved: using ${PROVIDER_LABELS[provider]} for AI Analyst and Insights.`);
  }

  function handleClear() {
    clearLlmConfig();
    setProvider("ollama");
    setApiKey("");
    setModel("");
    setSavedNotice("Reset to default: Ollama (free local model).");
  }

  return (
    <section aria-label="AI API Configuration">
      <div className="page-head">
        <div>
          <div className="eyebrow">Workspace settings</div>
          <h1>AI API Configuration</h1>
          <p>
            Uses Ollama (free local model) by default. Switch to Google Gemini or Anthropic Claude
            and provide your own API key anytime.
          </p>
        </div>
      </div>

      <form className="panel" style={{ maxWidth: "680px", padding: "22px" }} onSubmit={handleSave}>
        <div style={{ display: "grid", gap: "16px" }}>
          <div>
            <label
              htmlFor="llm-provider-select"
              style={{ display: "block", fontSize: "12px", fontWeight: 650, marginBottom: "6px" }}
            >
              AI Provider
            </label>
            <select
              id="llm-provider-select"
              name="llmProvider"
              className="select"
              style={{ width: "100%", padding: "9px 11px", fontSize: "12px" }}
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
            <div>
              <label
                htmlFor="llm-api-key-input"
                style={{ display: "block", fontSize: "12px", fontWeight: 650, marginBottom: "6px" }}
              >
                API Key (optional — leave blank to use server default)
              </label>
              <input
                id="llm-api-key-input"
                name="llmApiKey"
                type="password"
                autoComplete="off"
                className="select"
                style={{ width: "100%", padding: "9px 11px", fontSize: "12px" }}
                placeholder={KEY_PLACEHOLDERS[provider]}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
              />
              <small className="empty-note" style={{ display: "block", marginTop: "5px" }}>
                Stored only in this browser tab&apos;s sessionStorage and sent via request header.
                Never persisted to disk or logged.
              </small>
            </div>
          )}

          <div>
            <label
              htmlFor="llm-model-input"
              style={{ display: "block", fontSize: "12px", fontWeight: 650, marginBottom: "6px" }}
            >
              Model override (optional)
            </label>
            <input
              id="llm-model-input"
              name="llmModel"
              type="text"
              className="select"
              style={{ width: "100%", padding: "9px 11px", fontSize: "12px" }}
              placeholder={DEFAULT_MODELS[provider]}
              value={model}
              onChange={(e) => setModel(e.target.value)}
            />
          </div>

          <div className="actions" style={{ marginTop: "4px" }}>
            <button type="submit" className="btn primary">
              Save configuration
            </button>
            <button type="button" className="btn" onClick={handleClear}>
              Reset to Ollama default
            </button>
          </div>

          {savedNotice && (
            <div className="insight-card" role="status" aria-live="polite" style={{ marginTop: 0 }}>
              <div className="insight-head">✓ Configuration updated</div>
              <p>{savedNotice}</p>
            </div>
          )}
        </div>
      </form>
    </section>
  );
}
