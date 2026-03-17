---
doc-id: aion-lowering-v1
title: Lowering to Linalg (Skeleton)
tags: lowering, linalg, mlir
last-updated: 2026-03-17
---

# Lowering to Linalg (Skeleton)

The initial pass `aion-lower-to-linalg` demonstrates where `aion.pipe` chains would be lowered into vectorizable `linalg` operations.

Current Behavior
- Adds a marker attribute `aion.lowered` to `aion.pipe` ops to indicate the pass executed.

Building
- Build target: `AionLowering` (requires MLIR with Linalg dialect).
- Run with `mlir-opt -pass-pipeline='aion-lower-to-linalg'`.

Roadmap
- Recognize pure `map/filter/fold` sequences and lower to `linalg.generic` with parallel iterator types.
- Fuse adjacent stages when possible.
- Introduce shape inference and vectorization.

