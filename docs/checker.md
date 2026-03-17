---
doc-id: aion-checker-v1
title: Lightweight Type Checker
tags: checker, validation, null-safety, pipelines
last-updated: 2026-03-17
---

# Lightweight Type Checker

The interpreter ships with a lightweight checker to catch common issues early.

Rules
- Pipelines start from a function argument.
- `filter`/`map` reference the element via `?.` or `it`.
- `fold(init, expr)` uses both `acc` and the element.
- `sort` accepts a key expression (`it`) or comparator comparing `a` and `b`.
- `groupBy` requires a key expression referencing the element.
- `window(size[, step])` expects one or two numeric args.
- `pick(keyExpr)` selects from a map; requires a key expression.
- `match { ... }` requires proper arms `pat => expr`.
- `http.get(...)` must be followed immediately by `match`.
- `Array.get(i)` used as input to a pipeline must be followed by an immediate `match`.

These checks are conservative safeguards for AI agents and do not replace a full static type system.

