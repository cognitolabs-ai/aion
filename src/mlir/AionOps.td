//===- AionOps.td - Aion Dialect and Ops -----------------------*- tablegen -*-===//
// Minimal, clean ODS definitions for the Aion high-level dialect.

include "mlir/IR/OpBase.td"
include "mlir/Interfaces/SideEffectInterfaces.td"

// Dialect definition
def Aion_Dialect : Dialect {
  let name = "aion";
  let summary = "Aion High-Level Dialect for AI-native code generation.";
  let cppNamespace = "::mlir::aion";
}

// intent op: carries non-computable intent metadata (goal/pre/post) as strings.
def Aion_IntentOp : Op<Aion_Dialect, "intent", [NoSideEffect, IsolatedFromAbove]> {
  let summary = "Function intent metadata (goal, pre, post).";
  let description = [{
Carry the non-computable function intent expressed as strings
(Formal Query Language fragments). This op is metadata-only and
produces no results.
  }];

  let arguments = (ins StrAttr:$goal, StrAttr:$pre, StrAttr:$post);
  let results = (outs);

  // Example:  aion.intent goal = "...", pre = "...", post = "..."
  let assemblyFormat = "`goal` `=` $goal `,` `pre` `=` $pre `,` `post` `=` $post attr-dict";
}

// pipe op: models the `|` pipeline operator in the surface language.
def Aion_PipeOp : Op<Aion_Dialect, "pipe", [NoSideEffect]> {
  let summary = "Pipe input through a target function to produce output.";
  let description = [{
Takes an input SSA value and a symbol reference to a function-like
target. Conceptually represents `input | target` from the surface
language. Types are intentionally unconstrained here to allow
frontend-driven verification.
  }];

  let arguments = (ins AnyType:$input, SymbolRefAttr:$target);
  let results = (outs AnyType:$output);

  // Example:  %y = aion.pipe %x | @my.func : i32 -> i32
  let assemblyFormat = "$input `|` $target attr-dict `:` type($input) `->` type($output)";

  // Minimal semantic checks implemented in C++.
  let hasVerifier = 1;
}
