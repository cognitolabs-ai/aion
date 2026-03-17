---
doc-id: aion-structs-v1
title: Struct Literals
tags: structs, records, syntax
last-updated: 2026-03-17
---

# Struct Literals

Construct inline records using `Name{field: value, ...}` (type name is optional metadata at compile time).

Example
```
let items = [
  ProductStruct{id:"a",is_active:true,price:9.9},
  ProductStruct{id:"b",is_active:false,price:1.0}
]
```

Notes
- Fields are accessed with dot notation (`item.price`).
- In the interpreter, struct literals behave like maps with attribute access.

