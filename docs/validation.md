---
doc-id: aion-validation-v1
title: Native Validation (verify)
tags: verify, tests, sandbox, safety
last-updated: 2026-03-17
---

# Native Validation

Write executable tests directly after the function as a `verify { ... }` block.
- Runs in an isolated sandbox during compilation.
- Captures traces for self-correction on failure.
- Enforces null-safety and exhaustive matches.

Static Checks (Type Checker)
- Before execution, a lightweight checker validates pipeline well-formedness:
  - `filter`/`map` must reference the element via `?.` or `it`.
  - `fold` must include `acc` and an element reference.
  - `sort` accepts a key expression (`it`) or comparator using `a` and `b`.
  - `match` requires `{ pat => expr, ... }` arms.
  - Pipelines must start from a function argument.
