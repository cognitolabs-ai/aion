---
doc-id: aion-type-decls-v1
title: Struct Type Declarations
tags: types, structs, declarations
last-updated: 2026-03-17
---

# Struct Type Declarations

Declare record types for use in struct literals and type checking.

Syntax
```
struct ProductStruct { id: String, is_active: Bool, price: Float64 }
```

Location
- Place declarations in `types/standard.aiont` (loaded automatically by the interpreter).

Validation
- Struct literals like `ProductStruct{...}` are validated against declared fields. Missing or unknown fields raise errors.

