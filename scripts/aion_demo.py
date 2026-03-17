#!/usr/bin/env python3
"""
Aion demo CLI

Parses a minimal subset of Aion source (intent block, a single function
with a pipeline body, and an optional verify block) and emits a simple
MLIR-like textual IR using the `aion` dialect (`aion.intent`, `aion.pipe`).

Usage:
  python scripts/aion_demo.py examples/data_filter.aion --emit mlir
  python scripts/aion_demo.py examples/data_filter.aion --emit graph
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import List, Dict, Tuple


INTENT_START = re.compile(r"^\s*#intent\s*$")
INTENT_KV = re.compile(r"^\s*#\s*(goal|pre|post)\s*:\s*(.*)$")
FN_SIG = re.compile(r"^\s*fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*->\s*([^\{]+)\{\s*$")


class AionUnit:
    def __init__(self):
        self.intent: Dict[str, str] = {"goal": "", "pre": "", "post": ""}
        self.fn_name: str = ""
        self.fn_args: str = ""
        self.fn_ret: str = ""
        self.pipeline: List[str] = []
        self.input_var: str = ""


def parse_aion(path: Path) -> AionUnit:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    unit = AionUnit()

    i = 0
    n = len(lines)

    # Parse #intent block
    while i < n and not INTENT_START.match(lines[i]):
        i += 1
    if i < n and INTENT_START.match(lines[i]):
        i += 1
        while i < n:
            m = INTENT_KV.match(lines[i])
            if not m:
                break
            key, val = m.group(1), m.group(2).strip()
            unit.intent[key] = val
            i += 1

    # Parse function signature
    while i < n and not FN_SIG.match(lines[i]):
        i += 1
    if i >= n:
        raise ValueError("Missing function definition (fn ...)")
    m = FN_SIG.match(lines[i])
    unit.fn_name = m.group(1)
    unit.fn_args = m.group(2)
    unit.fn_ret = m.group(3).strip()
    i += 1

    # Parse function body until matching '}' (stop at verify or end)
    body_lines: List[str] = []
    brace_depth = 1
    while i < n and brace_depth > 0:
        line = lines[i]
        if line.strip().startswith("verify") and line.strip().endswith("{"):
            # stop body capture before verify block
            break
        brace_depth += line.count("{")
        brace_depth -= line.count("}")
        if brace_depth <= 0:
            break
        body_lines.append(line)
        i += 1

    # Extract pipeline expression from body lines
    body = "".join(l.strip() for l in body_lines if l.strip())
    # Body expected like: input | stage1(...) | stage2(...)
    if "|" not in body:
        raise ValueError("Demo expects a pipeline body using the '|' operator")
    segments = [seg.strip() for seg in body.split("|") if seg.strip()]
    unit.input_var = segments[0]
    unit.pipeline = segments[1:]
    return unit


def emit_mlir(unit: AionUnit) -> str:
    # For demo purposes, we use a placeholder type `!aion.any`.
    # This is a textual convention; it is not tied to a concrete MLIR type.
    ty = "!aion.any"
    lines: List[str] = []
    lines.append("module {")
    lines.append(f"  func @{unit.fn_name}(%arg0: {ty}) -> {ty} {{")
    goal = unit.intent.get("goal", "").replace('"', '\\"')
    pre = unit.intent.get("pre", "").replace('"', '\\"')
    post = unit.intent.get("post", "").replace('"', '\\"')
    lines.append(f"    aion.intent goal = \"{goal}\", pre = \"{pre}\", post = \"{post}\"")

    cur = "%arg0"
    vindex = 0
    for stage in unit.pipeline:
        # stage like: filter(?.price<=max_price)
        target = stage.split("(", 1)[0].strip()
        expr = ""
        if "(" in stage and stage.endswith(")"):
            expr = stage[stage.find("(") + 1 : -1].strip()
        out = f"%{vindex}"
        if expr:
            lines.append(
                f"    {out} = aion.pipe {cur} | @{target} {{expr = \"{expr.replace('"', '\\"')}\"}} : {ty} -> {ty}"
            )
        else:
            lines.append(f"    {out} = aion.pipe {cur} | @{target} : {ty} -> {ty}")
        cur = out
        vindex += 1

    lines.append(f"    return {cur}")
    lines.append("  }")
    lines.append("}")
    return "\n".join(lines) + "\n"


def emit_graph(unit: AionUnit) -> str:
    # Simple DOT graph of the pipeline
    lines = ["digraph aion_pipeline {", "  rankdir=LR;"]
    prev = unit.input_var
    lines.append(f"  \"{prev}\" [shape=box]")
    for idx, stage in enumerate(unit.pipeline, 1):
        label = stage.replace('"', '\\"')
        node = f"stage_{idx}"
        lines.append(f"  {node} [label=\"{label}\"]")
        lines.append(f"  \"{prev}\" -> {node}")
        prev = node
    lines.append("}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Aion demo: parse and emit MLIR-like IR")
    ap.add_argument("source", type=Path, help="Path to .aion source file")
    ap.add_argument("--emit", choices=["mlir", "graph", "summary"], default="mlir")
    args = ap.parse_args()

    unit = parse_aion(args.source)
    if args.emit == "mlir":
        print(emit_mlir(unit))
    elif args.emit == "graph":
        print(emit_graph(unit))
    else:
        print(f"Function: {unit.fn_name}")
        print(f"Intent: goal='{unit.intent.get('goal','')}', pre='{unit.intent.get('pre','')}', post='{unit.intent.get('post','')}'")
        print("Pipeline:")
        print("  input:", unit.input_var)
        for stage in unit.pipeline:
            print("  ->", stage)


if __name__ == "__main__":
    main()

