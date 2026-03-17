module {
  func @sort_active_by_price(%arg0: !aion.any) -> !aion.any {
    aion.intent goal = "Sort active products by ascending price.", pre = "data == Array[ProductStruct]", post = "return == Array[ProductStruct] where sorted by ?.price asc and ?.is_active==true"
    %0 = aion.pipe %arg0 | @filter {expr = "?.is_active==true"} : !aion.any -> !aion.any
    %1 = aion.pipe %0 | @sort {expr = "a.price < b.price"} : !aion.any -> !aion.any
    return %1
  }
}

