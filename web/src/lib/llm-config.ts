export type LlmProvider = "ollama" | "ollama_cloud" | "gemini" | "claude";

export interface LlmConfig {
  provider: LlmProvider;
  apiKey: string;
  model: string;
}

export const DEFAULT_MODELS: Record<LlmProvider, string> = {
  ollama: "llama3.2",
  ollama_cloud: "llama3.2",
  gemini: "gemini-2.5-flash",
  claude: "claude-3-5-sonnet-latest",
};

const STORAGE_KEY = "insightai_llm_config";

function parseProvider(value: unknown): LlmProvider {
  if (value === "gemini" || value === "claude" || value === "ollama" || value === "ollama_cloud") {
    return value;
  }
  return "ollama";
}

export function loadLlmConfig(): LlmConfig {
  if (typeof window === "undefined") {
    return { provider: "ollama", apiKey: "", model: "" };
  }
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return { provider: "ollama", apiKey: "", model: "" };
    const parsed = JSON.parse(raw) as Partial<LlmConfig>;
    return {
      provider: parseProvider(parsed.provider),
      apiKey: typeof parsed.apiKey === "string" ? parsed.apiKey : "",
      model: typeof parsed.model === "string" ? parsed.model : "",
    };
  } catch {
    return { provider: "ollama", apiKey: "", model: "" };
  }
}

export function saveLlmConfig(config: LlmConfig): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(config));
}

export function clearLlmConfig(): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(STORAGE_KEY);
}

export function getLlmHeaders(): Record<string, string> {
  const cfg = loadLlmConfig();
  const headers: Record<string, string> = { "X-LLM-Provider": cfg.provider };
  if (cfg.apiKey.trim()) headers["X-LLM-Api-Key"] = cfg.apiKey.trim();
  if (cfg.model.trim()) headers["X-LLM-Model"] = cfg.model.trim();
  return headers;
}
