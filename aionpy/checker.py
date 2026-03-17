from __future__ import annotations

import re
from typing import List

from .parser import Function, Stage


class TypeCheckError(Exception):
    pass


class TypeChecker:
    allowed_stages = {"filter", "map", "fold", "reduce", "sum", "sort", "match", "http.get", "groupBy", "window", "pick"}

    def __init__(self, fn: Function) -> None:
        self.fn = fn

    def run(self) -> None:
        self._check_signature()
        self._check_pipeline()

    def _check_signature(self) -> None:
        # Ensure input expression references one of the function args
        if not any(self.fn.input_expr.startswith(a) for a in self.fn.args):
            raise TypeCheckError("pipeline must start from a function argument")

    def _check_pipeline(self) -> None:
        # Null-safety: if input expr uses `.get(`, demand immediate `match` stage
        if '.get(' in self.fn.input_expr and (not self.fn.stages or self.fn.stages[0].name != 'match'):
            raise TypeCheckError("nullable value from 'get(...)' must be handled by an immediate match stage")

        for idx, st in enumerate(self.fn.stages):
            if st.name not in self.allowed_stages:
                # allow bare identifiers as future symbols, but warn via error for now
                raise TypeCheckError(f"unsupported stage: {st.name}")
            if st.name in ("filter", "map"):
                if not st.arg:
                    raise TypeCheckError(f"{st.name} requires an expression argument")
                if "?." not in st.arg and "it" not in st.arg:
                    raise TypeCheckError(f"{st.name} must reference the element via '?.' or 'it'")
            if st.name == "fold":
                if st.arg.count(',') < 1:
                    raise TypeCheckError("fold requires two arguments: initial, accumulator expression")
                if "acc" not in st.arg or ("?." not in st.arg and "it" not in st.arg):
                    raise TypeCheckError("fold accumulator must reference 'acc' and element '?.' or 'it'")
            if st.name == "sort":
                # optional comparator; if present and uses a/b, require both names
                if st.arg:
                    uses_a = re.search(r"\ba\b", st.arg) is not None
                    uses_b = re.search(r"\bb\b", st.arg) is not None
                    uses_it = ("?." in st.arg) or ("it" in st.arg)
                    if (uses_a or uses_b) and not (uses_a and uses_b):
                        raise TypeCheckError("sort comparator must reference both 'a' and 'b', or use 'it' as a key expression")
                    if not (uses_it or (uses_a and uses_b)):
                        raise TypeCheckError("sort arg must be a key expression with 'it' or a comparator using 'a' and 'b'")
            if st.name == "match":
                if not (st.arg.startswith('{') or '=>' in st.arg or st.raw.strip().endswith('}')):
                    raise TypeCheckError("match requires '{ ... }' with pattern arms 'pat => expr'")
            if st.name == "reduce":
                if st.arg.count(',') < 1:
                    raise TypeCheckError("reduce requires two arguments: initial, accumulator expression")
                if "acc" not in st.arg or ("?." not in st.arg and "it" not in st.arg):
                    raise TypeCheckError("reduce accumulator must reference 'acc' and element '?.' or 'it'")
            if st.name == "sum":
                # sum() or sum(expr) where expr references it
                if st.arg and ("?." not in st.arg and "it" not in st.arg):
                    raise TypeCheckError("sum expression must reference element via '?.' or 'it'")
            if st.name == "groupBy":
                if not st.arg or ("?." not in st.arg and "it" not in st.arg):
                    raise TypeCheckError("groupBy requires a key expression referencing '?.' or 'it'")
            if st.name == "window":
                # window(size [, step])
                parts = [p.strip() for p in st.arg.split(',') if p.strip()]
                if not (len(parts) == 1 or len(parts) == 2):
                    raise TypeCheckError("window expects 1 or 2 arguments: size [, step]")
            if st.name == "pick":
                if not st.arg:
                    raise TypeCheckError("pick requires a key expression, e.g., pick(1)")
            if st.name == "http.get":
                # Require the next stage to be a match for exhaustive handling
                if idx + 1 >= len(self.fn.stages) or self.fn.stages[idx + 1].name != 'match':
                    raise TypeCheckError("result of http.get must be handled by an immediate match stage")
