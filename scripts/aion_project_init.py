#!/usr/bin/env python3
"""
Aion Project Initializer

Bootstraps an AI‑assisted Aion project with:
- Environment checks (Python, Git, CMake, optional MLIR)
- Assistant provider config (Claude/Anthropic, OpenAI, or custom)
- Project template (Aion source, tests, README, .env, VS Code settings)
- Optional MCP server scaffold to expose repo docs to assistants (Claude Desktop)

Usage examples:
  python scripts/aion_project_init.py --name myapp --assistant claude --model claude-3-7-sonnet-latest \
      --description "Data pipeline service" --scope "MVP analytics" --with-mcp

  python scripts/aion_project_init.py --name demo --assistant openai --model gpt-4o

The script is safe to run multiple times; it won’t overwrite existing files unless --force is supplied.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


ROOT = Path(__file__).resolve().parents[1]


def sh(cmd: list[str]) -> tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return 0, out.decode(errors="ignore").strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        out = getattr(e, "output", b"")
        return 1, (out.decode(errors="ignore").strip() if out else str(e))


def check_env() -> dict:
    checks = {}
    py_ok = sys.version_info >= (3, 10)
    checks["python"] = (py_ok, f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    for tool in ("git", "cmake"):
        rc, out = sh([tool, "--version"])
        checks[tool] = (rc == 0, out.splitlines()[0] if out else "not found")

    # Optional MLIR
    rc1, out1 = sh(["mlir-opt", "--version"]) if shutil.which("mlir-opt") else (1, "mlir-opt not in PATH")
    mlir_dir = os.environ.get("MLIR_DIR", "")
    checks["mlir"] = (rc1 == 0 or bool(mlir_dir), out1 if rc1 == 0 else (mlir_dir or out1))

    return checks


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def write_file(path: Path, content: str, force: bool = False) -> None:
    if path.exists() and not force:
        return
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def scaffold_project(
    base: Path,
    name: str,
    description: str,
    scope: str,
    assistant: str,
    model: str,
    with_mcp: bool,
    with_precommit: bool,
    with_continue: bool,
    with_ci: bool,
    with_git: bool,
    template: str,
    with_bootstrap: bool,
    with_templates: bool,
    force: bool,
) -> None:
    proj = base / "projects" / name
    ensure_dir(proj)

    # README
    readme = dedent(f"""
    # {name}

    {description}

    ## Scope
    {scope}

    ## AI Assistant
    - Provider: {assistant}
    - Model: {model}

    ## Getting Started
    - Dev deps: `python -m pip install -r requirements-dev.txt`
    - Install pre-commit hooks: `pre-commit install`
    - Verify example: `python ../../scripts/aionc.py aion/main.aion --run verify`
    - Run function: `python ../../scripts/aionc.py aion/main.aion --run call --args "[[1,2,3]]"`
    {'- Run service: `uvicorn service.app:app --reload --port 8000`' if template == 'service' else ''}
    """)
    write_file(proj / "README.md", readme, force)

    # .env example
    env_example = dedent("""
    # Populate the keys below and copy to .env
    # Claude (Anthropic)
    ANTHROPIC_API_KEY=
    # OpenAI
    OPENAI_API_KEY=
    # Azure OpenAI
    AZURE_OPENAI_API_KEY=
    AZURE_OPENAI_ENDPOINT=
    # OpenRouter
    OPENROUTER_API_KEY=
    """)
    write_file(proj / ".env.example", env_example, force)

    # VS Code settings (recommend Continue extension and basic linting)
    vscode_settings = {
        "editor.formatOnSave": True,
        "python.analysis.typeCheckingMode": "basic",
        "files.associations": {"*.aion": "plaintext"},
        "extensions.recommendations": ["Continue.continue"],
    }
    write_file(proj / ".vscode" / "settings.json", json.dumps(vscode_settings, indent=2), force)

    # Assistant config (generic)
    assistant_cfg = {
        "assistant": assistant,
        "model": model,
        "style": {
            "commit_messages": "Conventional Commits",
            "reviews": "Actionable, concise, with risk callouts",
        },
        "context": {
            "docs": ["../../docs", "../../llms-full.txt"],
            "tests": ["tests"],
        },
    }
    write_file(proj / "assistant.yaml", json.dumps(assistant_cfg, indent=2), force)

    # Starter prompts for assistants
    prompts = {
        "coding.md": dedent("""
        BLUF: Implement the smallest change to satisfy intent and tests.
        - Always read the #intent block before coding.
        - Prefer pipelines (| map | filter | fold) over loops.
        - Enforce null-safety: handle get(...) and http results with match.
        - Add/adjust verify { ... } tests colocated with code.
        - Keep changes minimal, respect existing style.
        - Provide a short commit title and 1–3 bullets.
        """),
        "review.md": dedent("""
        Review checklist:
        - Does code match #intent goal/pre/post?
        - Are verify tests comprehensive and isolated?
        - Any nullable dereferences without match?
        - Are pipelines composable and side-effect free?
        - Minimal surface area, good names, docs updated.
        Risks & mitigations: list succinctly.
        """),
        "commit_message.md": dedent("""
        <type>(scope): short title

        - Why: BLUF context
        - What: key changes
        - Test: how verified (verify blocks / pytest)
        """),
        "planning.md": dedent("""
        Break down tasks into:
        - Spec alignment (#intent, types)
        - Code changes (files, ops)
        - Tests (verify blocks, pytest)
        - Docs (what pages to update)
        """),
    }
    for fname, content in prompts.items():
        write_file(proj / "prompts" / fname, content, force)

    # Aion source template
    aion_src = dedent("""
    #intent
    # goal: "Process metrics: drop negatives, double, sum."
    # pre: "metrics == Array[Int32]"
    # post: "return == Int32"
    fn main(metrics:Array[Int32])->Int32{
      metrics|filter(?.>=0)|map(?.*2)|fold(0, acc + ?.)
    }

    verify{
      assert main([1,-5,3,0])==8
      assert main([])==0
    }
    """)
    write_file(proj / "aion" / "main.aion", aion_src, force)

    # Tests (pytest invoking the interpreter)
    test_py = dedent("""
    from pathlib import Path
    import importlib

    def test_main_verify():
        aion = importlib.import_module('aionpy')
        u = aion.load_unit(Path('projects/{name}/aion/main.aion'))
        aion.Engine(u).run_verify()
    """
    ).replace("{name}", name)
    write_file(proj / "tests" / "test_main.py", test_py, force)

    # Dev requirements
    reqs = dedent("""
    pytest
    pre-commit
    black
    ruff
    mcp; python_version>='3.10'
    """)
    if template == 'service':
        reqs += "\nfastapi\nuvicorn\n"
    write_file(proj / "requirements-dev.txt", reqs, force)

    # .gitignore
    gitignore = dedent("""
    __pycache__/
    .pytest_cache/
    .venv/
    .env
    *.log
    """)
    write_file(proj / ".gitignore", gitignore, force)

    # Pre-commit config
    if with_precommit:
        precommit = dedent("""
        repos:
          - repo: https://github.com/pre-commit/pre-commit-hooks
            rev: v4.5.0
            hooks:
              - id: end-of-file-fixer
              - id: trailing-whitespace
          - repo: https://github.com/psf/black
            rev: 24.3.0
            hooks:
              - id: black
          - repo: https://github.com/astral-sh/ruff-pre-commit
            rev: v0.3.5
            hooks:
              - id: ruff
                args: [--fix]
          - repo: local
            hooks:
              - id: pytest
                name: run tests
                entry: python -m pytest -q
                language: system
                pass_filenames: false
        """)
        write_file(proj / ".pre-commit-config.yaml", precommit, force)

    # Continue config (optional)
    if with_continue:
        prov = "anthropic" if assistant == "claude" else ("openai" if assistant == "openai" else assistant)
        api_env = "ANTHROPIC_API_KEY" if prov == "anthropic" else ("OPENAI_API_KEY" if prov == "openai" else "OPENROUTER_API_KEY")
        cont_cfg = {
            "models": {
                "default": {
                    "provider": prov,
                    "model": model,
                    "apiKey": f"${{{api_env}}}",
                }
            },
            "tabAutocompleteModel": "default",
        }
        write_file(proj / ".continue" / "config.json", json.dumps(cont_cfg, indent=2), force)

    # VS Code tasks for quick actions
    tasks = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "Aion Verify",
                "type": "shell",
                "command": f"python ../../scripts/aionc.py aion/main.aion --run verify",
                "problemMatcher": []
            },
            {
                "label": "Aion Call",
                "type": "shell",
                "command": f"python ../../scripts/aionc.py aion/main.aion --run call --args '[[]]'",
                "problemMatcher": []
            },
            *([
              {
                "label": "Run Service",
                "type": "shell",
                "command": "uvicorn service.app:app --reload --port 8000",
                "problemMatcher": []
              }
            ] if template == 'service' else [])
        ]
    }
    write_file(proj / ".vscode" / "tasks.json", json.dumps(tasks, indent=2), force)

    # Makefile for common tasks
    makefile = dedent(f"""
    .PHONY: setup test verify call lint fmt hooks

    setup:
	python -m pip install -r requirements-dev.txt
	pre-commit install || true

    test:
	python -m pytest -q

    verify:
	python ../../scripts/aionc.py aion/main.aion --run verify

    call:
	python ../../scripts/aionc.py aion/main.aion --run call --args "[[1,2,3]]"

    lint:
	ruff check .

    fmt:
	black .

    hooks:
	pre-commit run --all-files || true
    {'\nserve:\n\tuvicorn service.app:app --reload --port 8000\n' if template == 'service' else ''}
    """)
    write_file(proj / "Makefile", makefile, force)

    # Per-project CI
    if with_ci:
        ci = dedent(f"""
        name: CI
        on: [push, pull_request]
        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/checkout@v4
              - uses: actions/setup-python@v5
                with:
                  python-version: '3.11'
              - name: Install deps
                working-directory: projects/{name}
                run: |
                  python -m pip install --upgrade pip
                  pip install -r requirements-dev.txt
              - name: Run tests
                working-directory: projects/{name}
                run: pytest -q
        """)
        write_file(proj / ".github" / "workflows" / "ci.yml", ci, force)

    # Initialize git (optional)
    if with_git:
        if not (proj / ".git").exists():
            sh(["git", "init", str(proj)])
        sh(["git", "-C", str(proj), "add", "."])
        sh(["git", "-C", str(proj), "commit", "-m", "chore(init): scaffold Aion AI-assisted project"])

    # Bootstrap scripts (optional)
    if with_bootstrap:
        boot_sh = dedent("""
        #!/usr/bin/env bash
        set -euo pipefail
        cd "$(dirname "$0")/.."
        python -m venv .venv
        source .venv/bin/activate
        python -m pip install --upgrade pip
        python -m pip install -r requirements-dev.txt
        pre-commit install || true
        python ../../scripts/aion_doctor.py --project .
        echo "Bootstrap complete. Activate venv: source .venv/bin/activate"
        """)
        write_file(proj / "scripts" / "bootstrap.sh", boot_sh, force)

        boot_ps = dedent("""
        # PowerShell bootstrap
        $ErrorActionPreference = 'Stop'
        $projRoot = (Resolve-Path (Join-Path (Split-Path $MyInvocation.MyCommand.Path -Parent) '..')).Path
        Set-Location $projRoot
        $py = Get-Command py -ErrorAction SilentlyContinue
        if ($py) { $pycmd = 'py'; $pyargs = '-3' } else { $pycmd = 'python'; $pyargs = '' }
        & $pycmd $pyargs -m venv .venv
        . .\.venv\Scripts\Activate.ps1
        & $pycmd $pyargs -m pip install --upgrade pip
        & $pycmd $pyargs -m pip install -r requirements-dev.txt
        pre-commit install
        & $pycmd $pyargs ../../scripts/aion_doctor.py --project .
        Write-Host "Bootstrap complete. Activate venv: . .\\.venv\\Scripts\\Activate.ps1"
        """)
        write_file(proj / "scripts" / "bootstrap.ps1", boot_ps, force)

    # Issue/PR templates (optional)
    if with_templates:
        bug = dedent("""
        ---
        name: Bug report
        about: Report a problem
        ---

        ## Summary
        
        ## Steps to reproduce
        
        ## Expected vs Actual
        
        ## Verify Block / Tests
        (Add or link to verify { ... } proving the bug and the fix.)
        """)
        write_file(proj / ".github" / "ISSUE_TEMPLATE" / "bug_report.md", bug, force)

        feat = dedent("""
        ---
        name: Feature request
        about: Propose an enhancement
        ---

        ## Intent
        Describe the #intent (goal, pre, post) for the new feature.

        ## Proposal
        Outline changes to Aion code, pipelines, and verify blocks.

        ## Risks & Mitigations
        """)
        write_file(proj / ".github" / "ISSUE_TEMPLATE" / "feature_request.md", feat, force)

        pr = dedent("""
        ## Summary

        - BLUF:

        ## Changes
        - 

        ## Tests
        - verify { ... } blocks updated/added
        - pytest results

        ## Intent Alignment
        - Goal/Pre/Post satisfied?

        ## Risks & Rollback
        """)
        write_file(proj / ".github" / "pull_request_template.md", pr, force)

    # MCP scaffold (Claude Desktop)
    if with_mcp:
        mcp_server = dedent("""
        #!/usr/bin/env python3
        """Aion MCP server (minimal): exposes docs/ and llms-full.txt as resources."""
        import os
        import sys
        from pathlib import Path
        try:
            from mcp.server.fastmcp import FastMCP
        except Exception as e:
            print("This server requires 'pip install mcp' (Anthropic MCP Python SDK).", file=sys.stderr)
            raise

        app = FastMCP("aion-mcp")

        ROOT = Path(__file__).resolve().parents[2]

        @app.resource("aion://docs/{path}")
        def get_doc(path: str):
            p = ROOT / 'docs' / path
            if not p.exists():
                raise FileNotFoundError(path)
            return p.read_text(encoding='utf-8')

        @app.resource("aion://spec/llms-full")
        def get_spec():
            return (ROOT / 'llms-full.txt').read_text(encoding='utf-8')

        if __name__ == "__main__":
            app.run()
        """)
        write_file(proj / "mcp" / "aion_mcp_server.py", mcp_server, force)

        servers_toml = dedent("""
        # Claude Desktop: add the following under mcpServers in your config
        # Example path (Windows): %APPDATA%/Claude/claude_desktop_config.json
        # Example path (macOS): ~/Library/Application Support/Claude/claude_desktop_config.json
        # Example path (Linux): ~/.config/Claude/claude_desktop_config.json

        # "aion-mcp": {
        #   "command": "python",
        #   "args": ["projects/{name}/mcp/aion_mcp_server.py"],
        #   "env": {{}}
        # }
        """).replace("{name}", name)
        write_file(proj / "mcp" / "servers.toml", servers_toml, force)

        # Registration helper (tries to patch Claude Desktop config)
        reg = dedent("""
        #!/usr/bin/env python3
        """Register Aion MCP server with Claude Desktop (optional)."""
        import json, os, sys
        from pathlib import Path

        def config_path():
            plat = sys.platform
            if plat == 'win32':
                appdata = os.environ.get('APPDATA')
                if not appdata:
                    return None
                return Path(appdata) / 'Claude' / 'claude_desktop_config.json'
            home = Path.home()
            if plat == 'darwin':
                return home / 'Library' / 'Application Support' / 'Claude' / 'claude_desktop_config.json'
            return home / '.config' / 'Claude' / 'claude_desktop_config.json'

        def main():
            cfgp = config_path()
            if not cfgp or not cfgp.exists():
                print('Claude Desktop config not found:', cfgp)
                print('Add this to mcpServers:')
                print(json.dumps({
                    'aion-mcp': {
                        'command': 'python',
                        'args': ['projects/{name}/mcp/aion_mcp_server.py'],
                        'env': {{}}
                    }
                }, indent=2))
                return 1
            data = json.loads(cfgp.read_text(encoding='utf-8'))
            servers = data.get('mcpServers') or {}
            servers['aion-mcp'] = {
                'command': 'python',
                'args': ['projects/{name}/mcp/aion_mcp_server.py'],
                'env': {{}}
            }
            data['mcpServers'] = servers
            cfgp.write_text(json.dumps(data, indent=2), encoding='utf-8')
            print('Registered aion-mcp in', cfgp)
            return 0

        if __name__ == '__main__':
            raise SystemExit(main())
        """
        ).replace("{name}", name)
        write_file(proj / "mcp" / "register_mcp.py", reg, force)

    # Service template assets
    if template == 'service':
        app_py = dedent("""
        from __future__ import annotations

        import json
        import sys
        from pathlib import Path
        from fastapi import FastAPI, HTTPException

        # Make the repo root importable
        REPO_ROOT = Path(__file__).resolve().parents[3]
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))

        from aionpy.engine import Engine, load_unit
        from aionpy.dot import DotDict, DotList

        PROJ_ROOT = Path(__file__).resolve().parents[1]
        AION_PATH = PROJ_ROOT / 'aion' / 'main.aion'

        app = FastAPI(title='Aion Service', version='0.1.0')

        # CORS (dev-friendly)
        try:
            from fastapi.middleware.cors import CORSMiddleware
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        except Exception:
            pass

        def to_plain(x):
            if isinstance(x, DotList) or isinstance(x, list):
                return [to_plain(v) for v in list(x)]
            if isinstance(x, DotDict) or isinstance(x, dict):
                return {k: to_plain(v) for k, v in dict(x).items()}
            return x

        def get_engine():
            unit = load_unit(AION_PATH)
            return Engine(unit)

        @app.get('/health')
        def health():
            return {'status': 'ok'}

        @app.post('/verify')
        def verify():
            try:
                get_engine().run_verify()
                return {'verify': 'PASS'}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        @app.post('/call')
        def call(payload: dict):
            args = payload.get('args') or []
            if not isinstance(args, list):
                raise HTTPException(status_code=400, detail='args must be a list')
            eng = get_engine()
            # Ensure function proxy created
            eng.run_verify()
            res = eng.env[eng.unit.name](*args)
            return {'result': to_plain(res)}
        """)
        write_file(proj / 'service' / 'app.py', app_py, force)

        svc_readme = dedent("""
        # Service Template

        FastAPI app that loads `aion/main.aion` and exposes:
        - `GET /health`
        - `POST /verify`
        - `POST /call` with JSON `{ "args": [...] }`

        Run:
          uvicorn service.app:app --reload --port 8000
        """)
        write_file(proj / 'service' / 'README.md', svc_readme, force)

        # OpenAPI export (no server needed)
        export_openapi = dedent("""
        from __future__ import annotations

        import json
        from pathlib import Path

        from fastapi.openapi.utils import get_openapi
        from service.app import app

        ROOT = Path(__file__).resolve().parents[1]
        out = ROOT / 'openapi.json'

        schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )
        out.write_text(json.dumps(schema, indent=2), encoding='utf-8')
        print('Wrote', out)
        """)
        write_file(proj / 'service' / 'export_openapi.py', export_openapi, force)

        # Python client
        py_client = dedent("""
        from __future__ import annotations

        import json
        from dataclasses import dataclass
        from typing import Any, List
        import requests

        @dataclass
        class AionClient:
            base_url: str

            def health(self) -> dict:
                r = requests.get(f"{self.base_url}/health")
                r.raise_for_status()
                return r.json()

            def verify(self) -> dict:
                r = requests.post(f"{self.base_url}/verify")
                r.raise_for_status()
                return r.json()

            def call(self, args: List[Any]) -> Any:
                r = requests.post(f"{self.base_url}/call", json={"args": args})
                r.raise_for_status()
                return r.json().get("result")

        if __name__ == "__main__":
            c = AionClient("http://localhost:8000")
            print("health:", c.health())
            print("verify:", c.verify())
            print("call:", json.dumps(c.call([[1, -5, 3, 0]])))
        """)
        write_file(proj / 'clients' / 'python' / 'client.py', py_client, force)

        # JS/TS client
        ts_client = dedent("""
        export class AionClient {
          constructor(readonly baseUrl: string) {}

          async health(): Promise<any> {
            const r = await fetch(`${this.baseUrl}/health`);
            if (!r.ok) throw new Error(`health failed: ${r.status}`);
            return r.json();
          }

          async verify(): Promise<any> {
            const r = await fetch(`${this.baseUrl}/verify`, { method: 'POST' });
            if (!r.ok) throw new Error(`verify failed: ${r.status}`);
            return r.json();
          }

          async call(args: any[]): Promise<any> {
            const r = await fetch(`${this.baseUrl}/call`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ args })
            });
            if (!r.ok) throw new Error(`call failed: ${r.status}`);
            const data = await r.json();
            return data.result;
          }
        }
        
        // Demo
        // const c = new AionClient('http://localhost:8000');
        // c.health().then(console.log)
        """)
        write_file(proj / 'clients' / 'js' / 'client.ts', ts_client, force)

        # docker-compose with reverse proxy
        compose = dedent(f"""
        services:
          api:
            image: python:3.11-slim
            working_dir: /app
            command: sh -lc "python -m pip install -r requirements-dev.txt && uvicorn service.app:app --host 0.0.0.0 --port 8000"
            environment:
              - PYTHONUNBUFFERED=1
              - PYTHONPATH=/repo
            ports:
              - "8000:8000"
            volumes:
              - ./:/app
              - ../../:/repo

          proxy:
            image: nginx:alpine
            depends_on:
              - api
            ports:
              - "8080:80"
            volumes:
              - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
        """)
        write_file(proj / 'docker-compose.yml', compose, force)

        nginx_conf = dedent("""
        server {
          listen 80;
          # Redirect root to Swagger UI
          location = / {
            return 302 /docs;
          }
          # Proxy all other routes
          location / {
            proxy_pass http://api:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
          }
        }
        """)
        write_file(proj / 'nginx.conf', nginx_conf, force)


def infer_defaults(assistant: str | None, model: str | None) -> tuple[str, str]:
    a = (assistant or "claude").lower()
    if a not in ("claude", "openai", "openrouter", "azureopenai"):
        a = "claude"
    if not model:
        model = {
            "claude": "claude-3-7-sonnet-latest",
            "openai": "gpt-4o",
            "openrouter": "anthropic/claude-3.7-sonnet",
            "azureopenai": "gpt-4o",
        }[a]
    return a, model


def main() -> None:
    ap = argparse.ArgumentParser(description="Initialize an AI-assisted Aion project")
    ap.add_argument("--name", required=True, help="Project name (folder under projects/)")
    ap.add_argument("--assistant", choices=["claude", "openai", "openrouter", "azureopenai"], default="claude")
    ap.add_argument("--model", help="Model id (e.g., claude-3-7-sonnet-latest, gpt-4o)")
    ap.add_argument("--description", default="A new Aion project")
    ap.add_argument("--scope", default="MVP")
    ap.add_argument("--with-mcp", action="store_true", help="Generate a minimal MCP server scaffold")
    ap.add_argument("--with-precommit", action="store_true", help="Add pre-commit config and dev requirements")
    ap.add_argument("--with-continue", action="store_true", help="Add a Continue extension config")
    ap.add_argument("--with-ci", action="store_true", help="Add a per-project GitHub Actions CI workflow")
    ap.add_argument("--git", action="store_true", help="Initialize a Git repository and make an initial commit")
    ap.add_argument("--template", choices=["library", "service"], default="library", help="Project template type")
    ap.add_argument("--with-bootstrap", action="store_true", help="Add bootstrap scripts (venv, deps, doctor)")
    ap.add_argument("--with-templates", action="store_true", help="Add GitHub issue/PR templates")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = ap.parse_args()

    assistant, model = infer_defaults(args.assistant, args.model)

    checks = check_env()
    print("Environment checks:")
    for k, (ok, info) in checks.items():
        mark = "OK" if ok else "MISSING"
        print(f" - {k:6s}: {mark} ({info})")

    # Assistant key guidance
    if assistant == "claude" and not os.environ.get("ANTHROPIC_API_KEY"):
        print("! Tip: Set ANTHROPIC_API_KEY in your environment or .env file for assistant integration.")
    if assistant == "openai" and not os.environ.get("OPENAI_API_KEY"):
        print("! Tip: Set OPENAI_API_KEY in your environment or .env file.")

    scaffold_project(
        ROOT,
        args.name,
        args.description,
        args.scope,
        assistant,
        model,
        args.with_mcp,
        args.with_precommit,
        args.with_continue,
        args.with_ci,
        args.git,
        args.template,
        args.with_bootstrap,
        args.with_templates,
        args.force,
    )
    print(f"\nProject scaffolded at projects/{args.name}")
    print("Next steps:")
    print(f"  1) Copy projects/{args.name}/.env.example to .env and fill API keys (if using an assistant)")
    print(f"  2) Open projects/{args.name} in VS Code; install 'Continue' extension (recommended)")
    if args.with_mcp:
        print(f"  3) (Claude Desktop) Add the server config from projects/{args.name}/mcp/servers.toml")
    print(f"  4) Run: python scripts/aionc.py projects/{args.name}/aion/main.aion --run verify")


if __name__ == "__main__":
    main()
