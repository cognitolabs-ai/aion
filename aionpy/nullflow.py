from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .parser import Function, Stage


class NullFlowError(Exception):
    pass


@dataclass
class FlowState:
    may_be_null: bool = False


def _expr_may_produce_null(expr: str) -> bool:
    if not expr:
        return False
    e = expr.replace(' ', '')
    # Heuristics: these operations may yield null
    return ('get(' in e) or ('.json(' in e) or ('null' in e)


class NullFlowChecker:
    def __init__(self, fn: Function) -> None:
        self.fn = fn

    def run(self) -> None:
        st = FlowState(may_be_null=('get(' in self.fn.input_expr))
        # Allow immediate filter removing nulls
        if st.may_be_null and self.fn.stages:
            s0 = self.fn.stages[0]
            if s0.name == 'filter' and ("!= null" in s0.arg or "is not null" in s0.arg):
                st.may_be_null = False

        for i, s in enumerate(self.fn.stages):
            # If current value may be null, require match now
            if st.may_be_null and s.name != 'match':
                raise NullFlowError(f"nullable value must be matched before stage '{s.name}'")

            # Update nullability based on this stage
            if s.name == 'match':
                st.may_be_null = False
            elif s.name == 'filter':
                # If filter removes nulls, future value is non-null
                if ("!= null" in s.arg) or ("is not null" in s.arg):
                    st.may_be_null = False
                else:
                    st.may_be_null = _expr_may_produce_null(s.arg)
            elif s.name in ('map', 'fold', 'sort', 'groupBy', 'window', 'pick', 'distinct', 'take', 'drop', 'flatten', 'zip'):
                st.may_be_null = _expr_may_produce_null(s.arg)
            elif s.name == 'http.get':
                st.may_be_null = False
