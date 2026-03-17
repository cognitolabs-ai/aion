---
doc-id: aion-strings-v1
title: Strings and Interpolation
tags: strings, interpolation, syntax
last-updated: 2026-03-17
---

# Strings and Interpolation

Aion supports string interpolation using `${expr}` inside quotes.

Example
```
"/api/users/${user_id}"
```

Notes
- Interpolation evaluates `expr` in the current scope.
- Use single or double quotes; escaping works as expected.

