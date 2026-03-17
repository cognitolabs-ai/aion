---
doc-id: aion-formatter-v1
title: Aion Formatter (MTS → Human)
tags: formatter, mts, dx
last-updated: 2026-03-17
---

# Formatter

Use `scripts/aion_format.py` to reflow pipelines and match blocks for readability without changing semantics.

Usage
```
python scripts/aion_format.py examples/data_filter.aion --write
```

What it does
- Breaks long pipelines across lines with indent on `|`.
- Normalizes `#intent` key spacing.
- Reflows `match { ... }` arms into one-per-line with trailing commas.

Roadmap
- Full pretty-printer with configurable whitespace and alignment.
- VS Code integration as a format-on-save provider.

