---
doc-id: aion-language-design-v1
title: Language Design (Dart + Python Influences)
tags: design, dart, python, null-safety, pipelines
last-updated: 2026-03-17
---

# Language Design (Dart + Python Influences)

Principles
- Sound Null Safety (Dart): `T?` is explicit; exhaustive handling via `match`/pipelines; dereferencing nullable without checks is rejected.
- Pragmatic Semantics (Python): familiar literals and operators, rich standard library semantics (arrays, maps), readable function calls.
- AI-Oriented Minimally Tokenized Syntax (Aion): drop visual bloat while keeping parseable structure; pipe-first orchestration.

Key Features
- `#intent` mandatory specification (goal/pre/post) with theorem-prover hooks.
- Pipelines `input | stage(args)` with `?.` element reference; higher-order ops `map`, `filter`, `fold`.
- Predictive Strong Typing via `infer` and whole-program resolution.
- Strict null safety at compile-time with `T?` and pattern matching.
- Native validation `verify { ... }` embedded near logic.

Mapping to This Repo
- Reference Interpreter (Python): executes a sizeable subset (pipelines, verify, mocks, http match). See `scripts/aionc.py` and `aionpy/`.
- MLIR Dialect: `aion.intent` and `aion.pipe` for IR-level mapping (see `src/mlir/`).

