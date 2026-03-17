---
doc-id: aion-types-v1
title: Type System (Predictive Strong Typing)
tags: types, infer, null-safety
last-updated: 2026-03-17
---

# Type System

Principles
- Predictive Strong Typing: `infer` placeholders resolved during compilation.
- Strict Null Safety: Nullable types are explicit (e.g., `T?`) and require exhaustive handling.
- Collections: `Array[T]` is homogeneous, bounds-safe; out-of-range reads yield `null`.

