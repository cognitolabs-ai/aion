#include "mlir/IR/BuiltinOps.h"
#include "mlir/IR/BuiltinAttributes.h"
#include "mlir/IR/PatternMatch.h"
#include "mlir/IR/SymbolTable.h"
#include "mlir/Pass/Pass.h"
#include "mlir/Dialect/Linalg/IR/Linalg.h"
#include "mlir/Dialect/Tensor/IR/Tensor.h"
#include "mlir/IR/Builders.h"
#include "mlir/IR/BuiltinTypes.h"
#include "mlir/Support/LogicalResult.h"

using namespace mlir;

namespace {
struct LowerPipeToMarker : OpRewritePattern<Operation> {
  using OpRewritePattern::OpRewritePattern;
  LogicalResult matchAndRewrite(Operation *op, PatternRewriter &rewriter) const override {
    // Placeholder: tag aion.pipe with a marker attribute to show pass ran.
    if (op->getName().getStringRef().equals("aion.pipe")) {
      op->setAttr("aion.lowered", rewriter.getUnitAttr());
      // Derive aion.stage from target symbol if present: @map, @filter, @fold, @sort
      if (auto sym = op->getAttrOfType<SymbolRefAttr>("target")) {
        auto leaf = sym.getLeafReference();
        if (!leaf.empty()) {
          op->setAttr("aion.stage", StringAttr::get(op->getContext(), leaf.str()));
        }
      }
      // Preserve `expr` attribute (if present) under a canonical name
      if (auto expr = op->getAttr("expr")) {
        op->setAttr("aion.expr", expr);
      }
      return success();
    }
    return failure();
  }
};

// Lower aion.pipe (stage == map) with tensor operands/results to linalg.generic
struct LowerMapPipeToLinalg : OpRewritePattern<Operation> {
  using OpRewritePattern::OpRewritePattern;
  LogicalResult matchAndRewrite(Operation *op, PatternRewriter &rewriter) const override {
    if (!op->getName().getStringRef().equals("aion.pipe"))
      return failure();
    // Only handle single-operand, single-result pipes
    if (op->getNumOperands() != 1 || op->getNumResults() != 1)
      return failure();
    // Stage must be 'map'
    auto stageAttr = op->getAttrOfType<StringAttr>("aion.stage");
    if (!stageAttr || stageAttr.getValue() != "map")
      return failure();
    auto inType = op->getOperand(0).getType().dyn_cast<RankedTensorType>();
    auto outType = op->getResult(0).getType().dyn_cast<RankedTensorType>();
    if (!inType || !outType || inType != outType || !inType.hasStaticShape())
      return failure();

    Location loc = op->getLoc();
    // Create tensor.empty for output
    SmallVector<int64_t, 4> shape(inType.getShape().begin(), inType.getShape().end());
    auto empty = rewriter.create<tensor::EmptyOp>(loc, shape, inType.getElementType());

    // Build indexing maps and iterator types (all parallel)
    unsigned rank = inType.getRank();
    SmallVector<AffineMap, 2> maps{
        AffineMap::getMultiDimIdentityMap(rank, rewriter.getContext()),
        AffineMap::getMultiDimIdentityMap(rank, rewriter.getContext())};
    SmallVector<Attribute, 4> iters;
    iters.reserve(rank);
    for (unsigned i = 0; i < rank; ++i)
      iters.push_back(StringAttr::get(rewriter.getContext(), "parallel"));

    // Create linalg.generic that yields identity (placeholder for expr lowering)
    auto generic = rewriter.create<linalg::GenericOp>(
        loc, outType, ValueRange{op->getOperand(0)}, ValueRange{empty.getResult()},
        rewriter.getAffineMapArrayAttr(maps), rewriter.getArrayAttr(iters));

    // Build region: ^bb0(inElem, outElem) { linalg.yield inElem : elemType }
    auto &region = generic.getRegion();
    auto elemTy = inType.getElementType();
    Block *body = new Block();
    body->addArgument(elemTy, loc);
    body->addArgument(elemTy, loc);
    region.push_back(body);
    OpBuilder::InsertionGuard guard(rewriter);
    rewriter.setInsertionPointToEnd(body);
    rewriter.create<linalg::YieldOp>(loc, body->getArgument(0));

    // Attach original expression (if any) for future lowering
    if (Attribute expr = op->getAttr("aion.expr"))
      generic->setAttr("aion.expr", expr);

    rewriter.replaceOp(op, generic.getResult(0));
    return success();
  }
};

struct AionLowerToLinalgPass : public PassWrapper<AionLowerToLinalgPass, OperationPass<ModuleOp>> {
  MLIR_DEFINE_EXPLICIT_INTERNAL_INLINE_TYPE_ID(AionLowerToLinalgPass)
  StringRef getArgument() const final { return "aion-lower-to-linalg"; }
  StringRef getDescription() const final { return "Lower aion.pipe to linalg (skeleton: adds a marker)"; }
  void runOnOperation() final {
    RewritePatternSet patterns(&getContext());
    patterns.add<LowerPipeToMarker, LowerMapPipeToLinalg>(&getContext());
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
