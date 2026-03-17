#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_init(name: str, template: str, assistant: str) -> int:
    # Sensible defaults per provider
    default_models = {
        "claude": "claude-3-7-sonnet-latest",
        "openai": "gpt-4o",
        "openrouter": "anthropic/claude-3.7-sonnet",
        "azureopenai": "gpt-4o",
    }
    model = default_models.get(assistant, default_models["claude"])    
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "aion_project_init.py"),
        "--name", name,
        "--assistant", assistant,
        "--model", model,
        "--template", template,
        "--with-mcp",
        "--with-precommit",
        "--with-continue",
        "--with-ci",
        "--git",
        "--with-bootstrap",
        "--with-templates",
        "--description", f"{template} project",
        "--scope", "MVP",
    ]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


def main() -> None:
    ap = argparse.ArgumentParser(description="Aion Quickstart")
    ap.add_argument("--name", required=True, help="Project name (under projects/)")
    ap.add_argument("--template", choices=["library", "service"], default="service")
    ap.add_argument("--assistant", choices=["claude", "openai", "openrouter", "azureopenai"], default="claude")
    args = ap.parse_args()

    rc = run_init(args.name, args.template, args.assistant)
    if rc != 0:
        sys.exit(rc)
    print(f"\nNext steps:\n  1) cd projects/{args.name} && ./scripts/bootstrap.sh (or scripts\\bootstrap.ps1 on Windows)\n  2) make verify (or VS Code tasks)\n  3) For service: uvicorn service.app:app --reload --port 8000")


if __name__ == "__main__":
    main()

