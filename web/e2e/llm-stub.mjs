/* global process, console */
// Deterministic Ollama-compatible stub for E2E and load tests (POST /api/chat).
// It answers by the JSON schema the API requests, so no real model is needed.
import { createServer } from "node:http";

const PORT = Number(process.env.LLM_STUB_PORT ?? 11500);
const REVENUE_SQL =
  "SELECT region, SUM(revenue) AS total_revenue FROM retail_sales GROUP BY region ORDER BY region";

function question(messages) {
  const user = messages.find((m) => m.role === "user")?.content ?? "";
  const match = user.match(/^Question: (.*)$/m);
  return {
    text: (match?.[1] ?? "").toLowerCase(),
    clarified: user.includes("User clarification:"),
  };
}

function answer(schema, messages) {
  const props = schema?.properties ?? {};
  const q = question(messages);
  if ("needs_clarification" in props) {
    const vague = q.text.includes("best") && !q.clarified;
    return {
      intent: "aggregate revenue",
      tables: ["retail_sales"],
      needs_clarification: vague,
      clarifying_question: vague ? "Best by revenue or by units sold?" : null,
      clarification_options: vague ? ["By total revenue", "By units sold"] : [],
    };
  }
  if ("sql" in props) {
    if (q.text.includes("delete")) return { sql: "DELETE FROM retail_sales", explanation: "" };
    if (q.text.includes("how many")) {
      return { sql: "SELECT COUNT(*) AS order_count FROM retail_sales", explanation: "" };
    }
    return { sql: REVENUE_SQL, explanation: "Revenue per region." };
  }
  if ("summary" in props) {
    return {
      summary: "Revenue is concentrated in a few regions.",
      key_findings: ["Regional totals differ noticeably."],
      next_questions: ["Which products drive the top region?"],
    };
  }
  return {};
}

const server = createServer((req, res) => {
  if (req.method === "GET" && req.url === "/health") {
    res.writeHead(200).end("ok");
    return;
  }
  if (req.method !== "POST" || req.url !== "/api/chat") {
    res.writeHead(404).end();
    return;
  }
  let body = "";
  req.on("data", (chunk) => (body += chunk));
  req.on("end", () => {
    const payload = JSON.parse(body || "{}");
    const content = JSON.stringify(answer(payload.format, payload.messages ?? []));
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(
      JSON.stringify({
        message: { role: "assistant", content },
        prompt_eval_count: 120,
        eval_count: 30,
      }),
    );
  });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`LLM stub listening on http://127.0.0.1:${PORT}`);
});
