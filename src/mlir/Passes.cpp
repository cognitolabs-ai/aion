#include "mlir/IR/BuiltinOps.h"
#include "mlir/Pass/Pass.h"

using namespace mlir;

namespace {
struct AionNopPass : public PassWrapper<AionNopPass, OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(AionNopPass)
  StringRef getArgument() const final { return "aion-nop"; }
  StringRef getDescription() const final { return "Aion no-op pass (skeleton)"; }
  void runOnOperation() final {
    // Intentionally empty
  }
};
} // namespace

std::unique_ptr<Pass> createAionNopPass() { return std::make_unique<AionNopPass>(); }

// Pass registration helper
namespace {
struct AionPassesRegistration {
  AionPassesRegistration() { PassRegistration<AionNopPass>(); }
} registerAionPasses;
} // namespace

