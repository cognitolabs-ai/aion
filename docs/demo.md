---
doc-id: aion-demo-v1
title: Aion Demo (IR Emitter)
tags: demo, cli, mlir, pipeline, intent
last-updated: 2026-03-17
---

# Aion Demo (IR Emitter)

This demo parses a small subset of the Aion language (intent + function with a pipeline body) and emits a minimal MLIR-like IR that uses the `aion` dialect.

## Run

- `python scripts/aion_demo.py examples/data_filter.aion --emit mlir`
- Optional: `--emit graph` generates a GraphViz DOT pipeline.

## Output (example)

```
module {
  func @filter_active_products(%arg0: !aion.any) -> !aion.any {
    aion.intent goal = "Filter a list of product records to find active items under a maximum price.", pre = "data == Array[ProductStruct], max_price == Float64", post = "return == Array[ProductStruct] where ?.is_active == true AND ?.price <= max_price"
    %0 = aion.pipe %arg0 | @filter {expr = "?.is_active==true"} : !aion.any -> !aion.any
    %1 = aion.pipe %0 | @filter {expr = "?.price<=max_price"} : !aion.any -> !aion.any
    return %1
  }
}
```

Notes
- `!aion.any` is a placeholder textual type for the demo only.
- The real `aion` dialect is defined in `src/mlir/AionOps.td` and is buildable if MLIR is present.

