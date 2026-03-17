---
doc-id: aion-semantics-v1
title: Aion Semantics (Overview)
tags: semantics, fql, sos, intent, verification
last-updated: 2026-03-17
---

# Aion Semantics (Overview)

BLUF: Aion binds non-computable intent (FQL) to executable logic and enforces safety via strict typing and native validation.

Key Points
- Intent as Specification: Every function declares `goal`, `pre`, and `post` in an `#intent` block. This forms the basis for theorem-prover checks and dynamic validation.
- Gradual Verification: If proof is inconclusive (Not Sure), the compiler delegates to an LLM or falls back to safe execution containers.
- Strict Null Safety: All nullable values are explicit (`T?`) and require exhaustive handling via `match` or pipelines.
- Pipeline Semantics: `input | stage(args)` composes pure transforms; stages are lowered to vectorizable forms (e.g., `linalg`).

Operational Sketch (SOS)
- State: ⟨env, store, value⟩
- Pipe: ⟨env, v | f⟩ → ⟨env, f(v)⟩ assuming f is total on v’s type; otherwise, reduce into error or nullable branch.
- Verify: Executes within an isolated sandbox, capturing traces on failure.

Axiomatic Sketch (Hoare-style)
- {pre ∧ wf(code)} code {post}
- wf(code) encodes well-formedness (types, null safety, totality of matches).
- The verifier constructs VC (verification conditions) from FQL and control-flow traces; failing VCs trigger self-correction.

Scope
- This doc provides the high-level model. See `docs/aion-dialect.md` for IR mapping and `docs/memory.md` for ownership rules.
