---
doc-id: aion-intent-v1
title: Intent Blocks (FQL)
tags: intent, fql, verification
last-updated: 2026-03-17
---

# Intent Blocks (FQL)

Every function begins with `#intent` declaring:
- `# goal:` human-readable objective
- `# pre:` input state/types
- `# post:` guaranteed output state/types

The compiler turns these into verification conditions; mismatches block lowering.

