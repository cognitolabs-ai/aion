---
doc-id: aion-intent-fql-v1
title: Intent FQL and Verification Conditions (MVP)
tags: fql, intent, vc, z3
last-updated: 2026-03-17
---

# Intent FQL (MVP)

This MVP supports basic postconditions and simple type/value constraints.

Supported Postconditions
- `return != null`
- `return == <Type>` where `<Type>` ∈ {Int, Int32, Float, Float64, Bool, String}
- `return == <Literal>` numbers or quoted strings
- Nullable types (`Type?`) allow `null`.
 - Numeric comparisons: `return >= N`, `>`, `<=`, `<`, `!=` (MVP)
 - Collection constraints (MVP): `where sorted by ?.field asc|desc`, simple element predicate `where ?.flag == true`

Integration
- The interpreter extracts `goal/pre/post` from `#intent` and checks the postcondition on function results observed in `verify` assertions.
- Violations are raised as `AssertionError` with a descriptive message.

Roadmap
- Parse and discharge quantified constraints (e.g., “for all x in data, x >= 0”).
- Integrate Z3 to solve numeric VCs.
- When proof is inconclusive (Not Sure), emit a structured MCP prompt with a minimal trace and the violated VC for assistant repair.
