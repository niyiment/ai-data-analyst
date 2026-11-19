---
name: add-validator-rule
description: Playbook for adding a single-purpose SQL safety rule to the AST validator pipeline.
---

# Add Validator Rule

## When to use

When adding a new SQL safety rule to the SQLGlot AST validator.

## Key steps

1. Create one rule file exposing the shared validator rule interface.
2. Register the rule in the validator pipeline.
3. Add table-driven passing, failing, and adversarial test cases mirroring the source layout.

## Checks

- Rule is single-purpose and fails closed on any doubt.
- Adversarial SQL suite remains 100% blocked.
- Any newly discovered bypass is added as a permanent regression test.
