---
name: add-golden-question
description: Playbook for adding a question and reference SQL to an evaluation golden set.
---

# Add Golden Question

## When to use

When growing an evaluation golden set for a demo dataset.

## Key steps

1. Add the question, reference SQL, category (`filter`, `aggregate`, `group by`, `join across sheets`, `date logic`, `ranking`, `ambiguity`), difficulty, and `order_sensitive` flag.
2. Confirm the reference SQL runs cleanly against the persistent `demo_<name>` schema under `analyst_ro`.

## Checks

- Result comparison is order-aware only when the question explicitly requires ordering.
- Reference SQL passes the AST validator.
