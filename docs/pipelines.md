---
doc-id: aion-pipelines-v1
title: Pipeline Operators
tags: pipeline, map, filter, fold, sort, groupBy, window, match
last-updated: 2026-03-17
---

# Pipeline Operators

Operators are composed left-to-right using `|`. The current element in element-wise stages is `?.` (or `it` in the interpreter).

- `map(expr)` → `Array[U]`
- `filter(pred)` → `Array[T]`
- `fold(init, expr)` → `U` (expr uses `acc` and `?.`)
- `reduce(init, expr)` → `U` (alias of `fold`)
- `sum([expr])` → `Number` (sum elements or key expression)
- `sort(expr)` → `Array[T]` (key mode with `it`) or comparator `a,b` mode: `a.price < b.price`.
- `groupBy(keyExpr)` → `Map[K, Array[T]]`
- `pick(keyExpr)` → Selects a value from a map by key.
- `window(size, step=1)` → `Array[Array[T]]`
- `match { pat => expr, ... }` → Branch on values (e.g., HTTP status) or `null`.

Examples

Filter + Sort
```
data|filter(?.is_active==true)|sort(a.price < b.price)
```

Group and Window
```
metrics|filter(?.>0)|groupBy(it%2)|map(it[1])|window(3)|map(it[0]+it[1]+it[2])
```

HTTP Handling
```
http.get("/api/users/${user_id}")|match{
  200=>?.json(),
  404=>null,
  _=>throw APIError("Unexpected: ${?.status}")
}
```
