cmake_minimum_required(VERSION 3.20)
project(Aion LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

option(AION_BUILD_DIALECT "Build Aion MLIR dialect (if MLIR is available)" ON)

if (AION_BUILD_DIALECT)
  find_package(MLIR QUIET CONFIG)
  if (MLIR_FOUND)
    message(STATUS "Found MLIR: ${MLIR_DIR}")
    add_subdirectory(src/mlir)
  else()
    message(STATUS "MLIR not found; skipping dialect build. Set MLIR_DIR to your MLIR config.")
  endif()
endif()

