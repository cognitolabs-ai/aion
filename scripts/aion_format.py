#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


PIPE_SPLIT = re.compile(r"\|(?![^(){}\[\]]*[\)\}\]])")


def format_pipeline_line(line: str) -> str:
    # Collapse spaces
    s = " ".join(line.strip().split())
    if "|" not in s:
        return s
    parts = [p.strip() for p in PIPE_SPLIT.split(s) if p.strip()]
    # Keep first on same line; others on new lines with indent
    out = []
    if parts:
        out.append(parts[0])
    for p in parts[1:]:
        out.append("  | " + p)
    return "\n".join(out)


def format_match_block(block: str, indent: str = "  ") -> str:
    inner = block.strip()[1:-1].strip()  # remove outer { }
    arms = [a.strip().rstrip(',') for a in inner.split(',') if a.strip()]
    lines = ["{"]
    for a in arms:
        lines.append(f"{indent}{a},")
    lines.append("}")
    return "\n".join(lines)


def format_file(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("#intent"):
            out.append("#intent")
            i += 1
            # Copy goal/pre/post lines verbatim with single space after '#'
            while i < len(lines) and lines[i].lstrip().startswith("#") and \
                  any(k in lines[i] for k in ("goal:", "pre:", "post:")):
                k = lines[i].lstrip()[1:].strip()
                out.append(f"# {k}")
                i += 1
            continue
        # Match block formatting
        if "| match" in ln and "{" in ln:
            # collect until matching '}'
            buf = [ln]
            depth = ln.count('{') - ln.count('}')
            i += 1
            while i < len(lines) and depth > 0:
                buf.append(lines[i])
                depth += lines[i].count('{') - lines[i].count('}')
                i += 1
            joined = "".join(b.strip() for b in buf)
            # split at '| match'
            head, _, rest = joined.partition("|match")
            rest = rest.strip()
            if rest.startswith("{"):
                rest_fmt = format_match_block(rest)
                out.append(format_pipeline_line(head) + " | match\n" + rest_fmt)
            else:
                out.append(format_pipeline_line(joined))
            continue
        # Pipeline formatting on simple lines
        out.append(format_pipeline_line(ln))
        i += 1
    # Ensure trailing newline
    res = "\n".join(out)
    if not res.endswith("\n"):
        res += "\n"
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description="Format Aion source (pipeline and match layout)")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--write", action="store_true", help="Overwrite files in place")
    args = ap.parse_args()

    for p in args.files:
        text = p.read_text(encoding="utf-8")
        fmt = format_file(text)
        if args.write:
            p.write_text(fmt, encoding="utf-8")
        else:
            sys.stdout.write(fmt)


if __name__ == "__main__":
    main()

