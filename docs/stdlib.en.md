---
doc-id: aion-stdlib-en-v1
title: Standard Library (EN)
tags: stdlib, arrays, pipelines
last-updated: 2026-03-17
---

# Array Module

BLUF: `Array[T]` is a homogeneous, bounds-safe dynamic buffer. Pipelines (`|`) replace loops and lower to `linalg` for vectorization.

Core Methods
- `len(self) -> Int32`
- `push(self, item: T) -> Void`
- `pop(self) -> T?` (nullable)
- `get(self, index: Int32) -> T?` (nullable)

Pipelines
- `map(expr)`
- `filter(pred)`
- `fold(init, expr)` / `reduce(init, expr)`
- `sort(key|cmp)`
- `groupBy(key)` → `Map[K, Array[T]]`
- `window(size[, step])` → `Array[Array[T]]`
- `pick(key)` → select from Map by key
- `sum([expr])`
- `distinct([key])`, `take(n)`, `drop(n)`, `flatten()`, `zip(other)`

Examples
```
metrics|filter(?. >= 0)|map(?.* 2)|fold(0, acc + ?.)
```

Null Safety
- Use `match { null => ..., val => ... }` when consuming nullable results (e.g., `get(0)`).

