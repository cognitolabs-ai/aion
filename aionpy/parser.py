from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


INTENT_START = re.compile(r"^\s*#intent\s*$")
INTENT_KV = re.compile(r"^\s*#\s*(goal|pre|post)\s*:\s*(.*)$")
FN_SIG = re.compile(r"^\s*fn\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*->\s*([^\{]+)\{\s*$")


@dataclass
class Stage:
    name: str
    arg: str = ""
    raw: str = ""


@dataclass
class VerifyStmt:
    kind: str
    payload: str


@dataclass
class Function:
    name: str
    args: List[str]
    ret: str
    input_expr: str
    stages: List[Stage]
    verify: List[VerifyStmt] = field(default_factory=list)
    intent: Dict[str, str] = field(default_factory=dict)
    arg_types: Dict[str, str] = field(default_factory=dict)
    ret_type: str = ""


def _split_stages(body: str) -> List[str]:
    parts: List[str] = []
    cur = []
    depth = 0
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == '|' and depth == 0:
            token = ''.join(cur).strip()
            if token:
                parts.append(token)
            cur = []
            i += 1
            continue
        if ch == '(' or ch == '{' or ch == '[':
            depth += 1
        elif ch == ')' or ch == '}' or ch == ']':
            depth -= 1
        cur.append(ch)
        i += 1
    token = ''.join(cur).strip()
    if token:
        parts.append(token)
    return parts


def _parse_pipeline(expr: str) -> (str, List[Stage]):
    parts = _split_stages(expr)
    if not parts:
        raise ValueError("pipeline expression is empty")
    input_expr = parts[0]
    stages: List[Stage] = []
    for stage in parts[1:]:
        name = stage
        arg = ""
        if '(' in stage and stage.endswith(')'):
            name = stage.split('(', 1)[0].strip()
            arg = stage[stage.find('(') + 1 : -1].strip()
        elif stage.startswith('match'):
            name = 'match'
            lb = stage.find('{')
            rb = stage.rfind('}')
            arg = stage[lb + 1 : rb].strip()
        stages.append(Stage(name=name, arg=arg, raw=stage))
    return input_expr, stages


def parse_file(path: Path) -> Function:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # intent
    intent: Dict[str, str] = {"goal": "", "pre": "", "post": ""}
    i = 0
    # Skip initial struct declarations
    while i < len(lines):
        if STRUCT_DECL.match(lines[i]):
            i += 1
            continue
        if INTENT_START.match(lines[i]):
            break
        # stop skipping when we reach other content
        if lines[i].strip() == '':
            i += 1
            continue
        break
    while i < len(lines) and not INTENT_START.match(lines[i]):
        i += 1
    if i < len(lines) and INTENT_START.match(lines[i]):
        i += 1
        while i < len(lines):
            m = INTENT_KV.match(lines[i])
            if not m:
                break
            intent[m.group(1)] = m.group(2).strip()
            i += 1

    # function sig
    while i < len(lines) and not FN_SIG.match(lines[i]):
        i += 1
    if i >= len(lines):
        raise ValueError("Missing function definition")
    m = FN_SIG.match(lines[i])
    fn_name = m.group(1)
    args_raw = m.group(2)
    ret = m.group(3).strip()
    args: List[str] = []
    arg_types: Dict[str, str] = {}
    if args_raw.strip():
        for a in args_raw.split(','):
            a = a.strip()
            if not a:
                continue
            if ':' in a:
                n, t = a.split(':', 1)
                n = n.strip()
                args.append(n)
                arg_types[n] = t.strip()
            else:
                args.append(a)
    i += 1

    # function body until '}' or 'verify'
    body_lines: List[str] = []
    depth = 1
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('verify') and line.strip().endswith('{'):
            break
        depth += line.count('{')
        depth -= line.count('}')
        if depth <= 0:
            break
        body_lines.append(line)
        i += 1
    body = ''.join(l.strip() for l in body_lines if l.strip())
    input_expr, stages = _parse_pipeline(body)

    # verify block (optional)
    verify: List[VerifyStmt] = []
    if i < len(lines) and lines[i].strip().startswith('verify'):
        i += 1  # skip 'verify {'
        # read until matching '}'
        vdepth = 1
        block_lines: List[str] = []
        while i < len(lines) and vdepth > 0:
            line = lines[i]
            vdepth += line.count('{')
            vdepth -= line.count('}')
            if vdepth <= 0:
                break
            if line.strip():
                block_lines.append(line.strip())
            i += 1
        # simple statements per line
        for bl in block_lines:
            if bl.startswith('assert_throws'):
                verify.append(VerifyStmt('assert_throws', bl))
            elif bl.startswith('assert'):
                verify.append(VerifyStmt('assert', bl))
            elif bl.startswith('mock'):
                verify.append(VerifyStmt('mock', bl))
            elif bl.startswith('let '):
                verify.append(VerifyStmt('let', bl))

    fn = Function(
        name=fn_name,
        args=args,
        ret=ret,
        input_expr=input_expr,
        stages=stages,
        verify=verify,
        intent=intent,
        arg_types=arg_types,
        ret_type=ret,
    )
    return fn


def parse_struct_decls(path: Path) -> Dict[str, Dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    decls: Dict[str, Dict[str, str]] = {}
    for line in text.splitlines():
        m = STRUCT_DECL.match(line)
        if not m:
            continue
        name = m.group(1)
        body = m.group(2)
        fields: Dict[str, str] = {}
        for part in body.split(','):
            part = part.strip()
            if not part or ':' not in part:
                continue
            fname, ftype = part.split(':', 1)
            fields[fname.strip()] = ftype.strip()
        if fields:
            decls[name] = fields
    return decls
STRUCT_DECL = re.compile(r"^\s*struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{(.*)\}\s*$")
