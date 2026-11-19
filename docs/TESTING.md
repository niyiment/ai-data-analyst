# Testing and Evaluation

## 9.1 Test layers

| Layer | Scope | Tooling |
| --- | --- | --- |
| Unit | Services, validator rules, sanitiser, type inference, chart-spec validator | `pytest` with fakes; `Vitest` on the frontend |
| Integration | Repositories, ingestion, executor limits, cleanup | `pytest` against PostgreSQL in Docker |
| API | Endpoint behaviour, ownership, error shapes | `pytest` with the ASGI test client |
| End to end | Upload, ask, chart, report happy path | Playwright against a local stack |
| Security | Adversarial SQL and authorisation suites | `pytest`, run in CI on every change |
| Evaluation | Golden sets with the live model | Runner, scheduled or manual, never in unit CI |

## 9.2 Evaluation design

- **Golden sets:** Around 30 questions per demo dataset, grouped by category (filter, aggregate, group by, join across sheets, date logic, ranking, ambiguity) and difficulty.
- **Correctness:** Compare *execution results* of generated and reference SQL, normalising column order and, unless the question demands order, row order.
- **Metrics:** Execution accuracy, validator rejection rate, clarification rate, failure categories, p50 and p95 latency, tokens per question.
- **Baselines:** Store every run with its prompt version and model so changes can be compared.
- **Gate:** A change to prompts or pipeline merges only if accuracy does not drop beyond an agreed tolerance.
