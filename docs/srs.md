---
doc-id: aion-srs-v1
title: Software Requirements (Summary)
tags: srs, requirements, ears
last-updated: 2026-03-17
---

# Software Requirements (Summary)

Functional (EARS)
- Parsing: On reading a `.aion` file, the compiler shall ignore visual whitespace and build an AST from MTS grammar.
- Intent: When parsing a function, the compiler shall reject it if a valid `#intent` block is missing.
- Gradual Verification: When the prover reaches a Not Sure state, the compiler shall query an LLM or apply a safe fallback.
- Predictive Types: When encountering `infer`, the backend shall resolve to strict types during compilation.

Non-functional
- Latency: Produce a human-readable preview in < 1ms for 500 tokens (IDE helper).
- Isolation: Execute `verify` blocks in an ephemeral sandbox (no network/filesystem access).
- Reliability: Do not emit executable IR when intent constraints are not proven.
