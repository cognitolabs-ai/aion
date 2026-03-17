from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from .dot import DotDict, DotList, wrap
from .parser import Function, Stage, VerifyStmt, parse_file
from .runtime import APIError, Response, http
from .checker import TypeChecker, TypeCheckError
from .nullflow import NullFlowChecker, NullFlowError
from .typesys import REGISTRY, load_standard_types


def _to_py_expr(expr: str) -> str:
    # Basic token replacements to Python
    s = expr
    s = s.replace('?.', 'it')
    s = s.replace('true', 'True')
    s = s.replace('false', 'False')
    s = s.replace('null', 'None')
    # Remove type-ascriptions like `as Type` (no-op in interpreter)
    s = re.sub(r"\s+as\s+[A-Za-z_][A-Za-z0-9_]*\??", "", s)
    return s


_STR_LIT = re.compile(r"^\s*([\'"])((?:.|\\\1)*?)\1\s*$")


def _interpolate_string(expr: str, env: Dict[str, Any]) -> str:
    m = _STR_LIT.match(expr)
    if not m:
        return expr
    quote, body = m.group(1), m.group(2)
    # Replace ${...} occurrences by evaluating inside env
    out: List[str] = []
    i = 0
    while i < len(body):
        if body[i] == '$' and i + 1 < len(body) and body[i + 1] == '{':
            j = i + 2
            depth = 1
            while j < len(body) and depth > 0:
                if body[j] == '{':
                    depth += 1
                elif body[j] == '}':
                    depth -= 1
                j += 1
            expr_inner = body[i + 2 : j - 1]
            val = _eval_expr(expr_inner, env)
            out.append(str(val))
            i = j
        else:
            out.append(body[i])
            i += 1
    return ''.join(out)


def _transform_struct_literals(expr: str) -> str:
    # Transform Name{a: 1, b: 2} -> __struct__('Name', {"a": 1, "b": 2})
    # Simple state machine handling nested braces; assumes no conflicting tokens in strings.
    out: List[str] = []
    i = 0
    in_string = False
    string_quote = ''
    while i < len(expr):
        ch = expr[i]
        if in_string:
            out.append(ch)
            if ch == string_quote and expr[i - 1] != '\\':
                in_string = False
            i += 1
            continue
        if ch in ('"', "'"):
            in_string = True
            string_quote = ch
            out.append(ch)
            i += 1
            continue
        # Look for Identifier{ pattern
        if ch.isalpha() or ch == '_':
            j = i + 1
            while j < len(expr) and (expr[j].isalnum() or expr[j] == '_'):
                j += 1
            # Skip whitespace
            k = j
            while k < len(expr) and expr[k].isspace():
                k += 1
            if k < len(expr) and expr[k] == '{':
                # emit __struct__('Name', {
                name = expr[i:j]
                out.append("__struct__('" + name + "', {")
                i = k + 1
                # Inside braces, ensure keys are quoted like key: -> "key":
                brace_depth = 1
                key_expected = True
                key_buf: List[str] = []
                while i < len(expr) and brace_depth > 0:
                    c = expr[i]
                    if c in ('"', "'"):
                        # copy quoted strings verbatim
                        q = c
                        out.append(c)
                        i += 1
                        while i < len(expr):
                            out.append(expr[i])
                            if expr[i] == q and expr[i - 1] != '\\':
                                i += 1
                                break
                            i += 1
                        continue
                    if c == '{':
                        brace_depth += 1
                        out.append(c)
                        i += 1
                        continue
                    if c == '}':
                        brace_depth -= 1
                        out.append('}')
                        if brace_depth == 0:
                            out.append(')')
                        i += 1
                        continue
                    # Quote unquoted keys before ':' at top level of this struct literal level
                    if c == ':' and brace_depth == 1:
                        # backtrack to find key start in out and quote it
                        # Find last segment since last '{' or ','
                        # Simplify: scan backwards to last '{' or ',' in out
                        p = len(out) - 1
                        # Trim whitespace
                        while p >= 0 and out[p].isspace():
                            p -= 1
                        # Accumulate key characters
                        key_chars: List[str] = []
                        while p >= 0 and (out[p].isalnum() or out[p] == '_'):
                            key_chars.append(out[p])
                            out.pop()
                            p -= 1
                        key = ''.join(reversed(key_chars))
                        out.append('"' + key + '"')
                        out.append(':')
                        i += 1
                        continue
                    out.append(c)
                    i += 1
                continue
            else:
                # Not a struct literal; copy identifier span
                out.append(expr[i:j])
                i = j
                continue
        out.append(ch)
        i += 1
    return ''.join(out)


def _eval_expr(expr: str, env: Dict[str, Any]) -> Any:
    # String interpolation first if it's a string literal with ${}
    if _STR_LIT.match(expr) and '${' in expr:
        return _interpolate_string(expr, env)
    code = _to_py_expr(_transform_struct_literals(expr))
    return eval(code, {}, env)


def _parse_value(val_src: str) -> Any:
    # For let and mock RHS
    s = val_src.replace('true', 'True').replace('false', 'False').replace('null', 'None')
    return ast.literal_eval(s)


def load_unit(path: Path) -> Function:
    # Load any struct declarations present in the file before parsing the function.
    try:
        from .parser import parse_struct_decls
        decls = parse_struct_decls(path)
        for name, fields in decls.items():
            REGISTRY.register_struct(name, fields)
    except Exception:
        # best-effort; parsing types is optional
        pass
    return parse_file(path)


class Engine:
    def __init__(self, unit: Function) -> None:
        self.unit = unit
        self.env: Dict[str, Any] = {}
        # expose runtime
        self.env.update({
            'APIError': APIError,
            'Response': Response,
        })

    def call(self, **kwargs: Any) -> Any:
        # Basic static checks before evaluation
        TypeChecker(self.unit).run()
        NullFlowChecker(self.unit).run()
        for name, val in kwargs.items():
            self.env[name] = wrap(val)
        # Evaluate pipeline
        cur = _eval_expr(self.unit.input_expr, self.env)
        cur = wrap(cur)
        for st in self.unit.stages:
            cur = self._apply_stage(st, cur)
        return wrap(cur)

    def _apply_stage(self, st: Stage, cur: Any) -> Any:
        if st.name == 'filter':
            assert isinstance(cur, (list, DotList)), "filter expects an array"
            out: List[Any] = []
            for el in cur:
                it = wrap(el)
                if _eval_expr(st.arg, {**self.env, 'it': it}):
                    out.append(it)
            return wrap(out)
        if st.name == 'map':
            assert isinstance(cur, (list, DotList)), "map expects an array"
            out2: List[Any] = []
            for el in cur:
                it = wrap(el)
                out2.append(_eval_expr(st.arg, {**self.env, 'it': it}))
            return wrap(out2)
        if st.name == 'fold':
            assert isinstance(cur, (list, DotList)), "fold expects an array"
            # fold(init, expr)
            parts = _split_args(st.arg)
            if len(parts) != 2:
                raise ValueError("fold expects two args: initial, expr")
            acc = _eval_expr(parts[0], self.env)
            for el in cur:
                it = wrap(el)
                acc = _eval_expr(parts[1], {**self.env, 'it': it, 'acc': acc})
            return acc
        if st.name == 'reduce':
            # same semantics as fold
            assert isinstance(cur, (list, DotList)), "reduce expects an array"
            parts = _split_args(st.arg)
            if len(parts) != 2:
                raise ValueError("reduce expects two args: initial, expr")
            acc = _eval_expr(parts[0], self.env)
            for el in cur:
                it = wrap(el)
                acc = _eval_expr(parts[1], {**self.env, 'it': it, 'acc': acc})
            return acc
        if st.name == 'sort':
            assert isinstance(cur, (list, DotList)), "sort expects an array"
            if not st.arg:
                return wrap(sorted(list(cur)))
            # if uses 'a'/'b' treat as comparator; otherwise treat as key expr using 'it'
            uses_a = 'a' in st.arg
            uses_b = 'b' in st.arg
            if uses_a and uses_b:
                from functools import cmp_to_key

                def cmp(a: Any, b: Any) -> int:
                    env = {**self.env, 'a': wrap(a), 'b': wrap(b)}
                    less_ab = _eval_expr(st.arg, env)
                    less_ba = _eval_expr(st.arg, {**self.env, 'a': wrap(b), 'b': wrap(a)})
                    if less_ab and not less_ba:
                        return -1
                    if less_ba and not less_ab:
                        return 1
                    return 0

                return wrap(sorted(list(cur), key=cmp_to_key(cmp)))
            else:
                def keyf(x: Any) -> Any:
                    return _eval_expr(st.arg, {**self.env, 'it': wrap(x)})

                return wrap(sorted(list(cur), key=keyf))
        if st.name == 'groupBy':
            assert isinstance(cur, (list, DotList)), "groupBy expects an array"
            buckets: Dict[Any, List[Any]] = {}
            for el in cur:
                it = wrap(el)
                key = _eval_expr(st.arg, {**self.env, 'it': it})
                buckets.setdefault(key, []).append(it)
            return wrap({k: wrap(v) for k, v in buckets.items()})
        if st.name == 'window':
            assert isinstance(cur, (list, DotList)), "window expects an array"
            parts = _split_args(st.arg)
            if not parts:
                raise ValueError("window requires at least size argument")
            size = int(_eval_expr(parts[0], self.env))
            step = int(_eval_expr(parts[1], self.env)) if len(parts) > 1 else 1
            data = list(cur)
            outw: List[Any] = []
            i = 0
            n = len(data)
            while i < n:
                w = data[i:i+size]
                if len(w) == size:
                    outw.append(wrap(w))
                i += step
            return wrap(outw)
        if st.name == 'sum':
            assert isinstance(cur, (list, DotList)), "sum expects an array"
            total = 0
            if st.arg:
                for el in cur:
                    it = wrap(el)
                    total += _eval_expr(st.arg, {**self.env, 'it': it})
            else:
                for el in cur:
                    total += el
            return total
        if st.name == 'pick':
            key = _eval_expr(st.arg, self.env)
            if isinstance(cur, dict):
                return wrap(cur.get(key))
            return None
        if st.name == 'match':
            # arg format: pattern => expr, pattern => expr, ...
            arms = _split_top_level_commas(st.arg)
            for arm in arms:
                pat, rhs = arm.split('=>', 1)
                pat = pat.strip()
                rhs = rhs.strip()
                matched = False
                if pat == '_':
                    matched = True
                else:
                    pv = _eval_expr(pat, {**self.env, 'it': cur})
                    # Match on value equality, status field, or None/null
                    if pv == cur or pv == getattr(cur, 'status', None):
                        matched = True
                if matched:
                    if rhs.startswith('throw '):
                        msg_expr = rhs[len('throw '):].strip()
                        ex = _eval_expr(msg_expr, self.env)
                        raise ex
                    return _eval_expr(rhs, {**self.env, 'it': cur})
            return None
        if st.name == 'http.get':
            # immediate call, return Response
            args = st.arg
            url = _eval_expr(args, self.env)
            return http.get(url)
        # Treat unknown as symbol ref function, not implemented
        return cur

    def run_verify(self) -> None:
        # Provide function callable into env
        def _fn_proxy(*call_args: Any) -> Any:
            # Map positional to named
            if len(call_args) != len(self.unit.args):
                raise TypeError("argument count mismatch")
            local_env = {name: wrap(val) for name, val in zip(self.unit.args, call_args)}
            # Save and restore env snapshot
            saved = dict(self.env)
            self.env.update(local_env)
            try:
                return self.call(**local_env)
            finally:
                self.env = saved

        self.env[self.unit.name] = _fn_proxy

        for stmt in self.unit.verify:
            if stmt.kind == 'mock':
                # mock http.get("/path") => Response(200, "{...}")
                m = re.match(r"mock\s+http\.get\((.*)\)\s*=>\s*Response\((.*)\)\s*", stmt.payload)
                if not m:
                    raise ValueError(f"invalid mock stmt: {stmt.payload}")
                url_expr, resp_args = m.group(1), m.group(2)
                url = _eval_expr(url_expr, self.env)
                parts = _split_args(resp_args)
                status = int(_eval_expr(parts[0], self.env)) if parts else 200
                body = _eval_expr(parts[1], self.env) if len(parts) > 1 else None
                http.mock(url, Response(status, body))
            elif stmt.kind == 'let':
                # let x = value (value may be an expression)
                m = re.match(r"let\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", stmt.payload)
                if not m:
                    raise ValueError(f"invalid let stmt: {stmt.payload}")
                name, val_src = m.group(1), m.group(2)
                val = _eval_expr(val_src, self.env)
                self.env[name] = wrap(val)
            elif stmt.kind == 'assert':
                # assert expr
                expr = stmt.payload[len('assert'):].strip()
                res = _eval_expr(expr, self.env)
                if not res:
                    raise AssertionError(f"assert failed: {expr}")
            elif stmt.kind == 'assert_throws':
                # assert_throws(APIError) { call }
                m = re.match(r"assert_throws\(([^)]+)\)\s*\{(.*)\}\s*", stmt.payload)
                if not m:
                    raise ValueError(f"invalid assert_throws: {stmt.payload}")
                ex_name = m.group(1).strip()
                call_expr = m.group(2).strip()
                expected = self.env.get(ex_name)
                if expected is None:
                    raise ValueError(f"unknown exception: {ex_name}")
                caught = None
                try:
                    _eval_expr(call_expr, self.env)
                except Exception as e:  # pylint: disable=broad-except
                    caught = e
                if not isinstance(caught, expected):
                    raise AssertionError(f"expected {ex_name} but got {type(caught).__name__ if caught else 'no exception'}")


def _split_args(arg_src: str) -> List[str]:
    # split top-level commas (respect parens/brackets/braces)
    return _split_top_level_commas(arg_src)


def _split_top_level_commas(src: str) -> List[str]:
    parts: List[str] = []
    cur: List[str] = []
    depth = 0
    for ch in src:
        if ch in '([{':
            depth += 1
        elif ch in ')]}':
            depth -= 1
        if ch == ',' and depth == 0:
            token = ''.join(cur).strip()
            if token:
                parts.append(token)
            cur = []
        else:
            cur.append(ch)
    token = ''.join(cur).strip()
    if token:
        parts.append(token)
    return parts
