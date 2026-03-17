---
doc-id: aion-ai-assist-v1
title: AI-Assisted Development Setup
tags: ai, assistants, claude, openai, mcp, continue
last-updated: 2026-03-17
---

# AI-Assisted Development Setup

This guide describes best practices for AI-assisted Aion development. It focuses on Claude (Anthropic) and OpenAI, and uses MCP and the Continue VS Code extension.

## Assistants

- Claude (Anthropic)
  - Strengths: long-context, strong code editing, MCP support in Claude Desktop.
  - API key: `ANTHROPIC_API_KEY` (add to `.env`).
- OpenAI (GPT-4 family)
  - Strengths: tool-using agents, broad ecosystem.
  - API key: `OPENAI_API_KEY`.

## Continue (VS Code)

- Install: extension `Continue`
- Configure Providers (GUI or JSON):
  - Anthropic with env var `ANTHROPIC_API_KEY`
  - OpenAI with `OPENAI_API_KEY`

## MCP (Model Context Protocol)

- Claude Desktop supports MCP servers to expose project context.
- This repo includes a minimal Python MCP server template in `projects/<name>/mcp/aion_mcp_server.py`.
- Install the SDK: `pip install mcp`
- Add server to Claude Desktop config (see `projects/<name>/mcp/servers.toml`).

## Project Init

- Use `scripts/aion_project_init.py` to scaffold a new project:
```
python scripts/aion_project_init.py --name demo --assistant claude --with-mcp \
  --model claude-3-7-sonnet-latest --description "Demo" --scope "MVP" --template service \
  --with-precommit --with-continue --with-ci --git --with-bootstrap --with-templates
```
- Then run verify with the reference interpreter:
```
python scripts/aionc.py projects/demo/aion/main.aion --run verify
```

## Best Practices

- Intent-first: Start every function with a precise `#intent` block.
- Verify early: Put concrete assertions in `verify { ... }` next to the code.
- Pipelines over loops: Use `| map | filter | fold` to enable MLIR lowering.
- Null handling: Treat `get()` and network calls as nullable; match immediately.
- Agent prompts: Include BLUF in comments to guide the assistant.
- Context: Expose docs and specs via MCP so assistants don’t hallucinate.
### Dev Experience

- Install dev deps: `python -m pip install -r projects/<name>/requirements-dev.txt`
- Install hooks: `pre-commit install` (run inside `projects/<name>`)
- Use prompt templates under `projects/<name>/prompts/` with your assistant (coding, review, commit_message, planning).
- Optional: Continue config at `projects/<name>/.continue/config.json`.
- Optional: Bootstrap scripts at `projects/<name>/scripts/bootstrap.sh` (Unix) and `bootstrap.ps1` (Windows PowerShell).
- Optional: Issue/PR templates at `projects/<name>/.github/`.

### Service Template

- Choose `--template service` to scaffold a FastAPI service that loads `aion/main.aion` and exposes `/health`, `/verify`, and `/call`.
- Run the service: `uvicorn service.app:app --reload --port 8000`
- Export OpenAPI (no server needed): `python projects/<name>/service/export_openapi.py` (writes `openapi.json`).
- Clients:
  - Python: `projects/<name>/clients/python/client.py`
  - JS/TS: `projects/<name>/clients/js/client.ts`
- Docker Compose:
  - `docker compose up` (serves API on :8000 and proxy on :8080)

### MCP Registration Helper

- If you used `--with-mcp`, a helper script is generated:
  - `projects/<name>/mcp/register_mcp.py`
  - It attempts to patch Claude Desktop’s `claude_desktop_config.json` to add the `aion-mcp` server (Windows/macOS/Linux default paths). Falls back to printing the JSON snippet if the config is not found.
