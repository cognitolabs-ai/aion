#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/PatternMatch.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Dialect/Linalg/IR/Linalg.h"

using namespace mlir;

namespace {
struct LowerPipeToMarker : OpRewritePattern<Operation> {
  using OpRewritePattern::OpRewritePattern;
  LogicalResult matchAndRewrite(Operation *op, PatternRewriter &rewriter) const override {
    // Placeholder: tag aion.pipe with a marker attribute to show pass ran.
    if (op->getName().getStringRef().equals("aion.pipe")) {
      op->setAttr("aion.lowered", rewriter.getUnitAttr());
      return success();
    }
    return failure();
  }
};

struct AionLowerToLinalgPass : public PassWrapper<AionLowerToLinalgPass, OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(AionLowerToLinalgPass)
  StringRef getArgument() const final { return "aion-lower-to-linalg"; }
  StringRef getDescription() const final { return "Lower aion.pipe to linalg (skeleton: adds a marker)"; }
  void runOnOperation() final {
    RewritePatternSet patterns(&getContext());
    patterns.add<LowerPipeToMarker>(&getContext());
    if (failed(applyPatternsAndFoldGreedily(getOperation(), std::move(patterns))))
      signalPassFailure();
  }
};
} // namespace

std::unique_ptr<Pass> createAionLowerToLinalgPass() { return std::make_unique<AionLowerToLinalgPass>(); }

namespace {
struct AionLoweringRegistration {
  AionLoweringRegistration() { PassRegistration<AionLowerToLinalgPass>(); }
} registerLowering;
} // namespace

