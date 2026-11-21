"""Load test for the AI Data Analyst API (Locust).

Each simulated user is an anonymous session that loads the sample dataset, then mixes
questions (validated SQL executed as analyst_ro), history and detail reads, and health
checks. Point the API at the deterministic LLM stub (web/e2e/llm-stub.mjs) so the test
measures this stack, not model latency. See loadtest/README.md.
"""

import os
import random

from locust import HttpUser, between, events, task
from locust.env import Environment

QUESTIONS = [
    "What is the revenue by region?",
    "How many orders are there?",
    "Show revenue per region",
    "How many orders were returned?",
]
MAX_FAILURE_RATIO = float(os.environ.get("LOAD_MAX_FAILURE_RATIO", "0.01"))
MAX_P95_MS = float(os.environ.get("LOAD_MAX_P95_MS", "1500"))
SESSION_COOKIE = "ada_session"


class AnalystUser(HttpUser):
    """One anonymous analyst session."""

    wait_time = between(0.5, 2.0)

    def on_start(self) -> None:
        resp = self.client.post("/api/v1/sessions", name="POST /sessions")
        token = resp.cookies.get(SESSION_COOKIE) or self.client.cookies.get(SESSION_COOKIE)
        # The cookie is Secure; requests will not send it over plain HTTP, so forward it.
        self.client.headers["Cookie"] = f"{SESSION_COOKIE}={token}"
        sample = self.client.post(
            "/api/v1/datasets/samples/retail_sales", name="POST /datasets/samples/{name}"
        )
        self.dataset_id = sample.json()["id"]

    def on_stop(self) -> None:
        self.client.delete("/api/v1/sessions/me", name="DELETE /sessions/me")

    @task(5)
    def ask_question(self) -> None:
        with self.client.post(
            f"/api/v1/datasets/{self.dataset_id}/queries",
            json={"question": random.choice(QUESTIONS)},
            name="POST /datasets/{id}/queries",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200 or resp.json().get("status") != "succeeded":
                resp.failure(f"query not answered: {resp.status_code} {resp.text[:120]}")

    @task(2)
    def read_history(self) -> None:
        self.client.get(
            f"/api/v1/datasets/{self.dataset_id}/queries", name="GET /datasets/{id}/queries"
        )

    @task(2)
    def read_dataset(self) -> None:
        self.client.get(f"/api/v1/datasets/{self.dataset_id}", name="GET /datasets/{id}")

    @task(1)
    def health(self) -> None:
        self.client.get("/health", name="GET /health")


@events.quitting.add_listener
def enforce_budgets(environment: Environment, **_: object) -> None:
    """Fail the run (exit code 1) when error rate or p95 latency exceeds the budget."""
    total = environment.stats.total
    p95 = total.get_response_time_percentile(0.95) or 0
    problems = []
    if total.fail_ratio > MAX_FAILURE_RATIO:
        problems.append(f"failure ratio {total.fail_ratio:.2%} > {MAX_FAILURE_RATIO:.2%}")
    if p95 > MAX_P95_MS:
        problems.append(f"p95 {p95:.0f} ms > {MAX_P95_MS:.0f} ms")
    if problems:
        print("LOAD BUDGET FAILED: " + "; ".join(problems))
        environment.process_exit_code = 1
    else:
        print(f"LOAD BUDGET MET: failures {total.fail_ratio:.2%}, p95 {p95:.0f} ms")
