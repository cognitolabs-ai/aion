---
doc-id: aion-null-safety-v1
title: Null Safety
tags: null, safety, match, types
last-updated: 2026-03-17
---

# Null Safety

Principles
- Nullable values are explicit (`T?`) and must be handled via `match` or guards.
- Array bounds access returns `null` (safe), requiring handling.
- Network operations may fail; exhaustive `match` branches are required.

Interpreter Rules
- Access from `Array.get(i)` may produce `None`; the type checker demands an immediate `match` stage if used as a pipeline input.
- Results of `http.get(...)` require an immediate `match` stage.

Example
```
data.get(0)|match{null=>0, val=>val}
```

