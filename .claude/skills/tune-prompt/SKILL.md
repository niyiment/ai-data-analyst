---
name: tune-prompt
description: Playbook for versioning and evaluating a prompt template change.
---

# Tune Prompt

## When to use

When modifying any LLM prompt template (plan, SQL generation, chart spec, or insights).

## Key steps

1. Create a new versioned prompt template file (never inline prompts in service code).
2. Run the evaluation suite against the golden sets using the new prompt version.
3. Compare execution accuracy, rejection rate, latency, and token cost against the stored baseline.

## Checks

- No accuracy regression beyond the agreed tolerance.
- Token cost and prompt version are recorded in `eval_runs`.
