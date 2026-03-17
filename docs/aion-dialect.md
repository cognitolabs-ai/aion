---
doc-id: aion-mlir-dialect-v1
title: Aion MLIR Dialect Overview
tags: mlir, dialect, ops, intent, pipeline
last-updated: 2026-03-17
---

# Aion MLIR Dialect

This document describes the initial MLIR dialect used by the Aion compiler to represent high-level, AI-native semantics.

## Dialect

- Name: `aion`
- Namespace: `::mlir::aion`
- Purpose: Carry intent metadata and model the surface pipeline operator (`|`) before lowering to standard/`linalg` dialects.

## Operations

1) aion.intent
- Summary: Non-computable metadata for function intent (goal, preconditions, postconditions).
- Traits: `NoSideEffect`, `IsolatedFromAbove`
- Operands: none
- Results: none
- Attributes:
  - `goal`: `StrAttr`
  - `pre`: `StrAttr`
  - `post`: `StrAttr`
- Assembly:
  - `aion.intent goal = "...", pre = "...", post = "..."`

2) aion.pipe
- Summary: Models the surface `input | target` pipeline application.
- Traits: `NoSideEffect`
- Operands:
  - `$input`: `AnyType`
- Results:
  - `$output`: `AnyType`
- Attributes:
  - `target`: `SymbolRefAttr` (function-like symbol)
- Assembly:
  - `%y = aion.pipe %x | @my.func : type(%x) -> type(%y)`

## Mapping from Surface Syntax

- Surface:
  - `#intent` block on a function → `aion.intent` op attached near function entry in the IR.
  - `data | map(...) | filter(...)` → A chain of `aion.pipe` nodes referencing function-like symbols for transformation stages, later lowered into vectorizable ops (e.g., `linalg`).

## Notes

- The dialect is intentionally minimal to unblock frontend work and TableGen generation. Additional traits and verifiers can be added as the compiler evolves.
- A skeleton pass `aion-nop` is provided (no-op). Once MLIR is installed, you can build `AionPasses` and run via `mlir-opt -pass-pipeline='aion-nop'`.
