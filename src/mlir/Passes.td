//===- Passes.td - Aion Dialect Passes ------------------------*- tablegen -*-===//

include "mlir/Pass/PassBase.td"

def CreateAionNopPass : Pass<"aion-nop", "mlir::ModuleOp"> {
  let summary = "Aion no-op pass (skeleton)";
  let description = [{
Performs no transformations; serves as a placeholder for future
lowerings (e.g., aion.pipe -> linalg).
  }];
}

