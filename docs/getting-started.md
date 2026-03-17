---
doc-id: aion-getting-started-v1
title: Getting Started
tags: setup, demo, mlir, build
last-updated: 2026-03-17
---

# Getting Started

Two paths: run the Python demo, or build the MLIR dialect.

## Run the Demo (No Dependencies)
- Requires Python 3.9+
- `python scripts/aion_demo.py examples/data_filter.aion --emit mlir`

## Build the Dialect (Optional)
- Requires LLVM/MLIR with CMake config (`MLIR_DIR`).
- `cmake -S . -B build -DAION_BUILD_DIALECT=ON -DMLIR_DIR=<path>`
- `cmake --build build --target AionDialect`

