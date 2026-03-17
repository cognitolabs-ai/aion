def Aion_Dialect : Dialect { let name = "aion"; let summary = "Aion High-Level Dialect for AI-native code generation."; let cppNamespace = "::mlir::aion"; }
def Aion_IntentOp : Op<Aion_Dialect, "intent", [IsolatedFromAbove]> { let arguments = (ins StringAttr:goal,StringAttr:precondition, StringAttr:$postcondition); }
def Aion_PipeOp : Op<Aion_Dialect, "pipe", [NoSideEffect]> { let arguments = (ins AnyType:input 
v
​
 al,SymbolRefAttr:target_func); let results = (outs AnyType:output 
v
​
 al);letassemblyFormat="input_val | target 
f
​
 uncattr−dict‘:‘type(input_val) -> type($output_val)"; } 