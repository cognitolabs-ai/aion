#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
python "$DIR/aion_demo.py" "$DIR/../examples/data_filter.aion" --emit mlir

