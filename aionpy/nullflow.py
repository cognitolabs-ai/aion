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
        st = FlowState()
        # Start state: input may be null if it uses `.get(`
        st.may_be_null = 'get(' in self.fn.input_expr
        if st.may_be_null and (not self.fn.stages or self.fn.stages[0].name != 'match'):
            raise NullFlowError("nullable input (from get(...)) must be handled by an immediate match stage")

        for i, s in enumerate(self.fn.stages):
            # If current value may be null, we require an immediate match
            if st.may_be_null and s.name != 'match':
                raise NullFlowError(f"nullable value must be matched before stage '{s.name}'")

            # Update nullability based on this stage
            if s.name == 'match':
                st.may_be_null = False
            elif s.name in ('filter', 'map', 'fold', 'sort', 'groupBy', 'window', 'pick'):
                st.may_be_null = _expr_may_produce_null(s.arg)
            elif s.name == 'http.get':
                # http.get returns Response (non-null), but requires match for branches (enforced by TypeChecker)
                st.may_be_null = False

