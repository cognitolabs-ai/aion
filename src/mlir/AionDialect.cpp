// MLIR core includes
#include "mlir/IR/Builders.h"
#include "mlir/IR/BuiltinAttributes.h"
#include "mlir/IR/BuiltinTypes.h"
#include "mlir/IR/DialectImplementation.h"
#include "mlir/IR/FunctionInterfaces.h"
#include "mlir/IR/SymbolTable.h"

// Dialect registration and hooks
#include "AionOpsDialect.h.inc"

// Op declarations/definitions generated from TableGen
#include "AionOps.h.inc"
#include "AionOps.cpp.inc"

using namespace mlir;
using namespace mlir::aion;

// Verifier for Aion_PipeOp: ensure symbol resolves to a function-like op
// and that its signature matches (1 input -> 1 output) and types align.
LogicalResult Aion_PipeOp::verify() {
  Operation *op = getOperation();
  SymbolRefAttr symRef = getTargetAttr();
  Operation *resolved = SymbolTable::lookupNearestSymbolFrom(op, symRef);
  if (!resolved)
    return emitOpError("target symbol not found: ") << symRef;

  auto funcIface = dyn_cast<FunctionOpInterface>(resolved);
  if (!funcIface)
    return emitOpError("target does not implement FunctionOpInterface: ") << symRef;

  auto fTy = dyn_cast<FunctionType>(funcIface.getFunctionType());
  if (!fTy)
    return emitOpError("target does not have a FunctionType: ") << symRef;

  if (fTy.getNumInputs() != 1 || fTy.getNumResults() != 1)
    return emitOpError("expected target to have (1 input -> 1 result) signature");

  Type inTy = getInput().getType();
  Type outTy = getOutput().getType();
  if (fTy.getInput(0) != inTy || fTy.getResult(0) != outTy)
    return emitOpError("type mismatch: expected ") << inTy << " -> " << outTy
                   << ", but target has " << fTy;

  return success();
}
