import { beforeEach, describe, expect, it } from "vitest";
import { clearLlmConfig, getLlmHeaders, loadLlmConfig, saveLlmConfig } from "./llm-config";

const DEFAULT = { provider: "ollama", apiKey: "", model: "" };

describe("llm-config", () => {
  beforeEach(() => window.sessionStorage.clear());

  it("shows Ollama as the starting choice but sends no override until one is saved", () => {
    // Sending a provider by default would override the server's LLM_PROVIDER (production bug).
    expect(loadLlmConfig()).toEqual(DEFAULT);
    expect(getLlmHeaders()).toEqual({});
  });

  it("round-trips a saved config and clears it", () => {
    saveLlmConfig({ provider: "claude", apiKey: "k", model: "m" });
    expect(loadLlmConfig()).toEqual({ provider: "claude", apiKey: "k", model: "m" });

    clearLlmConfig();
    expect(loadLlmConfig()).toEqual(DEFAULT);
    expect(getLlmHeaders()).toEqual({});
  });

  it("keeps keys in sessionStorage only, never localStorage", () => {
    saveLlmConfig({ provider: "gemini", apiKey: "secret", model: "" });

    expect(window.localStorage.length).toBe(0);
    expect(window.sessionStorage.length).toBe(1);
  });

  it("falls back safely on corrupt or unknown stored values", () => {
    window.sessionStorage.setItem("insightai_llm_config", "{not json");
    expect(loadLlmConfig()).toEqual(DEFAULT);

    window.sessionStorage.setItem(
      "insightai_llm_config",
      JSON.stringify({ provider: "evil", apiKey: 42, model: null }),
    );
    expect(loadLlmConfig()).toEqual(DEFAULT);
    expect(getLlmHeaders()).toEqual({});
  });

  it("omits blank key and model headers", () => {
    saveLlmConfig({ provider: "ollama_cloud", apiKey: "   ", model: "" });

    expect(getLlmHeaders()).toEqual({ "X-LLM-Provider": "ollama_cloud" });
  });
});
