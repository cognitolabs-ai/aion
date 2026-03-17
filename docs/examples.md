---
doc-id: aion-examples-v1
title: Examples Index
tags: examples, pipelines, http
last-updated: 2026-03-17
---

# Examples

- `examples/data_filter.aion`: Filtering with pipelines and `#intent`.
- `examples/network_call.aion`: HTTP match handling and `verify` mocks (illustrative).
- `examples/process_metrics.aion`: Numeric pipeline with `filter|map|fold` and passing `verify`.
- `examples/sort_products.aion`: Sorting with comparator (`a.price < b.price`).
- `examples/aggregate.aion`: Sum prices of active products with `sum(?.price)`.
- `examples/inline_structs.aion`: Inline `struct` declaration used in pipelines.
- `examples/get_safe_first.aion`: Safe indexing via `match` on `data.get(0)`.
- `examples/non_null_filter.aion`: Null-elimination via `filter(it != null)` followed by `fold`.
