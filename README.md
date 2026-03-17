# Aion Programming Language

Aion is the world's first AI-native programming language designed specifically for Large Language Models and agentic workflows.

## Repository Structure
- `docs/`: Technical specifications, architecture, and tutorials.
- `include/aion/`: Public C++ headers for the Aion compiler.
- `src/`: LLVM/MLIR backend and frontend source code.
- `examples/`: Demonstrations of Aion's Minimally Tokenized Syntax.
- `tests/`: The Aion Vericoding Benchmark Suite.
- `scripts/`: Utilities and the demo CLI (`aion_demo.py`).
  - `aionc.py`: reference interpreter for the minimal subset (verify runner).

## For AI Agents
If you are an LLM or an agentic tool (e.g., Cursor, Copilot), please refer to `llms-full.txt` for the complete, machine-readable language specification.

## Quick Demo (IR)

- Prerequisite: Python 3.9+
- Run: `python scripts/aion_demo.py examples/data_filter.aion --emit mlir`
- Output: Minimal MLIR-like IR using the `aion` dialect (`aion.intent`, `aion.pipe`).

Notes
- The demo is self-contained and does not require an MLIR toolchain.
- If you have MLIR installed, you can also build the real dialect library via CMake (see `CMakeLists.txt`).

## Run the Interpreter (Subset)

- Linux/macOS: `python scripts/aionc.py examples/process_metrics.aion --run verify`
- Windows (if `python` not found): `py -3 scripts\aionc.py examples\process_metrics.aion --run verify`
- Expects: `verify: PASS`

More Examples
- Sorting: `python scripts/aionc.py examples/sort_products.aion --run verify`
- HTTP and match: `python scripts/aionc.py examples/network_call.aion --run verify`
- Group + Window: `python scripts/aionc.py examples/group_by_window.aion --run verify`
- Aggregation: `python scripts/aionc.py examples/aggregate.aion --run verify`

Call Mode
- You can run a function and print its JSON result:
  - `python scripts/aionc.py examples/process_metrics.aion --run call --args "[[1,-5,3,0]]"`
  - Outputs: `8`

## Project Scaffold

- Initialize a new AI-assisted project:
  - `python scripts/aion_project_init.py --name demo --assistant claude --with-mcp --model claude-3-7-sonnet-latest --description "Demo" --scope "MVP"`
  - See `docs/ai-assist.md` for setup details (Claude Desktop MCP, Continue extension).

Quickstart Wrapper
- One command to scaffold with recommended flags:
  - `python scripts/aion_quickstart.py --name demo --template service --assistant claude`

## Environment Doctor
- Run quick checks for tools, packages, and a project’s verify:
  - Global: `python scripts/aion_doctor.py`
  - Project: `python scripts/aion_doctor.py --project projects/demo`

## Documentation Pointers
- Pipelines: `docs/pipelines.md`
- Null Safety: `docs/null-safety.md`
- Structs: `docs/structs.md`
- Strings: `docs/strings.md`
- Type Declarations: `docs/type-decls.md` (loaded from `types/standard.aiont`)
