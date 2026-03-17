module {
  func @filter_active_products(%arg0: !aion.any) -> !aion.any {
    aion.intent goal = "Filter a list of product records to find active items under a maximum price.", pre = "data == Array[ProductStruct], max_price == Float64", post = "return == Array[ProductStruct] where ?.is_active == true AND ?.price <= max_price"
    %0 = aion.pipe %arg0 | @filter {expr = "?.is_active==true"} : !aion.any -> !aion.any
    %1 = aion.pipe %0 | @filter {expr = "?.price<=max_price"} : !aion.any -> !aion.any
    return %1
  }
}

