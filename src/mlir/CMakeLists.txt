if (NOT MLIR_FOUND)
  return()
endif()

include(TableGen)
include(MLIR)
include(AddMLIR)

set(LLVM_TARGET_DEFINITIONS AionOps.td)
mlir_tablegen(AionOps.h.inc -gen-op-decls)
mlir_tablegen(AionOps.cpp.inc -gen-op-defs)
mlir_tablegen(AionOpsDialect.h.inc -gen-dialect-decls -dialect=aion)
mlir_tablegen(AionOpsDialect.cpp.inc -gen-dialect-defs -dialect=aion)
add_public_tablegen_target(AionOpsIncGen)

add_mlir_library(AionDialect
  AionDialect.cpp
  DEPENDS
    AionOpsIncGen
  LINK_LIBS PUBLIC
    MLIRIR
    MLIRFunctionInterfaces
)

# Generate dialect docs (if BUILD_DOC is enabled in your environment)
add_mlir_doc(AionOps AionOps Dialects/ -gen-op-doc)

# Convenience target to force ODS generation without building libs
add_custom_target(ods-check DEPENDS AionOpsIncGen)

# Optional pass library
set(LLVM_TARGET_DEFINITIONS Passes.td)
mlir_tablegen(Passes.h.inc -gen-pass-decls -name Aion)
add_public_tablegen_target(AionPassesIncGen)

add_mlir_library(AionPasses
  Passes.cpp
  DEPENDS AionPassesIncGen
  LINK_LIBS PUBLIC MLIRIR)

add_mlir_library(AionLowering
  LowerToLinalg.cpp
  LINK_LIBS PUBLIC
    MLIRIR
    MLIRLinalg
    MLIRTensor)
