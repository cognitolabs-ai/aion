#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any, Dict


def read_message() -> Dict[str, Any]:
    headers = {}
    while True:
        line = sys.stdin.readline()
        if line == "\r\n" or line == "\n":
            break
        name, _, value = line.partition(":")
        headers[name.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    body = sys.stdin.read(length)
    return json.loads(body)


def write_message(payload: Dict[str, Any]) -> None:
    data = json.dumps(payload)
    sys.stdout.write(f"Content-Length: {len(data)}\r\n\r\n{data}")
    sys.stdout.flush()


def extract_intent(text: str) -> str:
    lines = text.splitlines()
    goal = ""
    capture = False
    for ln in lines:
        if ln.strip() == "#intent":
            capture = True
            continue
        if capture and ln.lstrip().startswith("#") and "goal:" in ln:
            goal = ln.split(":", 1)[1].strip()
            break
        if capture and ln.strip() and not ln.lstrip().startswith("#"):
            break
    return goal


def on_initialize(req):
    return {
        "capabilities": {
            "textDocumentSync": 1,
            "hoverProvider": True,
            "diagnosticProvider": {"interFileDependencies": False, "workspaceDiagnostics": False},
        }
    }


def on_hover(params):
    text = params.get("textDocument", {}).get("text", "")
    goal = extract_intent(text)
    return {"contents": {"kind": "markdown", "value": f"Intent: {goal}"}}


def on_diagnostic(params):
    # Very minimal: flag missing #intent
    text = params.get("textDocument", {}).get("text", "")
    diags = []
    if "#intent" not in text:
        diags.append({
            "severity": 2,
            "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
            "message": "Missing #intent block",
        })
    return {"kind": "full", "items": diags}


def main():
    while True:
        req = read_message()
        method = req.get("method")
        if method == "initialize":
            res = on_initialize(req)
            write_message({"jsonrpc": "2.0", "id": req.get("id"), "result": res})
        elif method == "textDocument/hover":
            write_message({"jsonrpc": "2.0", "id": req.get("id"), "result": on_hover(req.get("params", {}))})
        elif method == "textDocument/diagnostic":
            write_message({"jsonrpc": "2.0", "id": req.get("id"), "result": on_diagnostic(req.get("params", {}))})
        elif method == "shutdown":
            write_message({"jsonrpc": "2.0", "id": req.get("id"), "result": None})
            break
        else:
            # Notification or unhandled
            if "id" in req:
                write_message({"jsonrpc": "2.0", "id": req.get("id"), "result": None})


if __name__ == "__main__":
    main()

