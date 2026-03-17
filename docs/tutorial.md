---
doc-id: aion-tutorial-v1
title: Aion Tutorial (First Pipeline)
tags: tutorial, quickstart, pipeline, verify
last-updated: 2026-03-17
---

# First Pipeline in Aion

Write a function with an `#intent` block, then compose transforms using `|`.

Example

```aion
#intent
# goal: Filter active products under a price.
# pre: data == Array[ProductStruct], max_price == Float64
# post: return == Array[ProductStruct]
fn filter_active_products(data:Array[ProductStruct],max_price:Float64)->Array[ProductStruct]{
  data|filter(?.is_active==true)|filter(?.price<=max_price)
}

verify{
  // Mocks and asserts go here (executed in sandbox by the compiler)
}
```

Try It
- `python scripts/aion_demo.py examples/data_filter.aion --emit mlir`
- Read the generated IR to see `aion.intent` and `aion.pipe`.

Sorting Example

```aion
#intent
# goal: Sort active products by ascending price.
# pre: data == Array[ProductStruct]
# post: return == Array[ProductStruct]
fn sort_active_by_price(data:Array[ProductStruct])->Array[ProductStruct]{
  data|filter(?.is_active==true)|sort(a.price < b.price)
}
```

Run verify
- `python scripts/aionc.py examples/sort_products.aion --run verify`
