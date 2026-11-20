# Load test

A [Locust](https://locust.io/) scenario for the API. Each simulated user:

1. Creates an anonymous session and loads the `retail_sales` sample.
2. Asks questions, which go through the AST validator and run on `analyst_ro`.
3. Reads query history and the dataset's detail, and calls the health check.
4. Deletes its data on exit.

The run fails (exit code 1) if more than 1% of requests fail, or if p95 latency exceeds 1500 ms. Override these with `LOAD_MAX_FAILURE_RATIO` and `LOAD_MAX_P95_MS`.

## Run locally

Use the deterministic LLM stub so the test measures this stack rather than model latency. Raise the per-session question limit, or the rate limiter will (correctly) reject the load.

```bash
docker compose up -d postgres            # with migrations applied
node web/e2e/llm-stub.mjs &               # Ollama-compatible stub on :11500

cd api
API_PORT=8001 LLM_PROVIDER=ollama OLLAMA_BASE_URL=http://127.0.0.1:11500 \
  OLLAMA_MODEL=load-stub QUESTIONS_PER_SESSION_PER_HOUR=100000 LLM_DAILY_CALL_BUDGET=1000000 \
  uv run python -m app &

cd ..
uv run --with locust locust -f loadtest/locustfile.py --host http://127.0.0.1:8001 \
  --headless --users 25 --spawn-rate 5 --run-time 60s --only-summary
```

Locust is not a project dependency: `uv run --with locust` runs it in a temporary environment. Drop `--headless` to use the web UI at http://localhost:8089.

## Testing the limits

To check that the protections hold under load, run once with the default limits (30 questions per session per hour). Questions beyond the limit should return `429 RATE_LIMITED`. Those show up as failures, which is the expected behaviour in that run.
