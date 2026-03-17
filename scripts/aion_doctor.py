#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def sh(cmd: list[str]) -> tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return 0, out.decode(errors="ignore").strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        out = getattr(e, "output", b"")
        return 1, (out.decode(errors="ignore").strip() if out else str(e))


def check_tool(name: str, args: list[str] = ["--version"]) -> tuple[bool, str]:
    if not shutil.which(name):
        return False, "not found in PATH"
    rc, out = sh([name] + args)
    return rc == 0, (out.splitlines()[0] if out else "ok")


def read_assistant_cfg(proj: Path) -> tuple[str|None, str|None]:
    p = proj / "assistant.yaml"
    if not p.exists():
        return None, None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("assistant"), data.get("model")
    except Exception:
        return None, None


def detect_template(proj: Path) -> str:
    if (proj / "service" / "app.py").exists():
        return "service"
    return "library"


def pip_check(mod: str) -> tuple[bool, str]:
    try:
        __import__(mod)
        return True, "installed"
    except Exception as e:
        return False, str(e)


def main() -> None:
    ap = argparse.ArgumentParser(description="Aion environment doctor")
    ap.add_argument("--project", type=Path, default=None, help="Path to scaffolded project (projects/<name>)")
    args = ap.parse_args()

    print("Aion Doctor\n===========")

    # Python
    py_ok = sys.version_info >= (3, 10)
    print(f"python: {'OK' if py_ok else 'MISSING'} ({sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro})")

    # Tools
    for tool in ("git", "cmake"):
        ok, info = check_tool(tool)
        print(f"{tool:6s}: {'OK' if ok else 'MISSING'} ({info})")

    # MLIR (optional)
    if shutil.which("mlir-opt") or os.environ.get("MLIR_DIR"):
        ok, info = check_tool("mlir-opt") if shutil.which("mlir-opt") else (True, f"MLIR_DIR={os.environ.get('MLIR_DIR')}")
        print(f"mlir  : {'OK' if ok else 'MISSING'} ({info})")
    else:
        print("mlir  : OPTIONAL (install LLVM/MLIR to build dialects)")

    # Dev Python packages (best-effort)
    for mod in ("pytest", "pre_commit", "black", "ruff"):
        ok, info = pip_check(mod)
        print(f"pip:{mod:10s} {'OK' if ok else 'MISSING'} ({info})")

    # Project-specific
    if args.project:
        proj = args.project
        print(f"\nProject: {proj}")
        assistant, model = read_assistant_cfg(proj)
        if assistant:
            print(f"assistant: {assistant} ({model or 'model not set'})")
        template = detect_template(proj)
        print(f"template : {template}")

        # Assistant env vars
        if assistant == "claude" and not os.environ.get("ANTHROPIC_API_KEY"):
            print("env     : ANTHROPIC_API_KEY MISSING (set in shell or .env)")
        if assistant == "openai" and not os.environ.get("OPENAI_API_KEY"):
            print("env     : OPENAI_API_KEY MISSING (set in shell or .env)")

        # Service deps
        if template == "service":
            for mod in ("fastapi", "uvicorn"):
                ok, info = pip_check(mod)
                print(f"pip:{mod:10s} {'OK' if ok else 'MISSING'} ({info})")

        # MCP
        if (proj / "mcp" / "aion_mcp_server.py").exists():
            ok, info = pip_check("mcp")
            print(f"pip:mcp      {'OK' if ok else 'MISSING'} ({info})")
            print("MCP     : If using Claude Desktop, run register script in mcp/.")

        # Verify runnable
        aion_main = proj / "aion" / "main.aion"
        if aion_main.exists():
            rc, out = sh([sys.executable, str(Path(__file__).resolve().parents[0] / "aionc.py"), str(aion_main), "--run", "verify"])  # noqa: E501
            print(f"verify : {'PASS' if rc == 0 else 'FAIL'}")
            if rc != 0:
                print(out)

    print("\nHints\n-----")
    print("- Use scripts/aion_project_init.py to scaffold new projects.")
    print("- For service template: uvicorn service.app:app --reload --port 8000")
    print("- For MCP with Claude Desktop: projects/<name>/mcp/register_mcp.py")


if __name__ == "__main__":
    main()

