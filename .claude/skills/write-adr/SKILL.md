---
name: write-adr
description: Playbook for recording a significant architectural decision in docs/adr/.
---

# Write ADR

## When to use

When making or changing a significant architectural decision.

## Key steps

1. Copy `docs/adr/0000-template.md` to `docs/adr/NNNN-short-title.md` using the next sequential number.
2. Fill in Status, Date, Context, Decision, and Consequences.
3. Link the new ADR from any affected docs.
4. If replacing an existing decision, mark the old ADR as `Superseded` (do not edit its decision text).

## Checks

- Number is next in sequence.
- Old ADR is marked `Superseded` with a link to the new ADR if replaced.
