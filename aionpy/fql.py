from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class FQLSpec:
    goal: str = ""
    pre: str = ""
    post: str = ""

    @staticmethod
    def from_intent(intent: Dict[str, str]) -> "FQLSpec":
        return FQLSpec(goal=intent.get("goal", ""), pre=intent.get("pre", ""), post=intent.get("post", ""))

    def check_post(self, value: Any) -> Optional[str]:
        """Return error string if violated, else None. Implements a minimal subset:
        - "return == <Type>" → isinstance check for int/float/str/bool
        - "return != null" → ensure value is not None
        - "return == <Literal>" → equality to simple literal
        - "T?" postfix in type (nullable) allows None
        """
        post = (self.post or "").strip()
        if not post:
            return None

        # return != null
        if re.search(r"return\s*!=\s*null", post):
            if value is None:
                return "Postcondition failed: return must not be null"

        # return == Type or Type?
        m = re.search(r"return\s*==\s*([A-Za-z_][A-Za-z0-9_\?]*)", post)
        if m:
            tname = m.group(1)
            allow_null = tname.endswith("?")
            if value is None and allow_null:
                return None
            if value is None and not allow_null:
                return "Postcondition failed: return must be non-null"
            base = tname.rstrip("?")
            py = {
                "Int": int,
                "Int32": int,
                "Float": float,
                "Float64": float,
                "Bool": bool,
                "String": str,
            }.get(base)
            if py and not isinstance(value, py):
                return f"Postcondition failed: return expected {base}, got {type(value).__name__}"

        # return == literal (number or quoted)
        m2 = re.search(r"return\s*==\s*(\d+(?:\.\d+)?)", post)
        if m2:
            try:
                lit = float(m2.group(1)) if "." in m2.group(1) else int(m2.group(1))
                if value != lit:
                    return f"Postcondition failed: return expected {lit}, got {value}"
            except Exception:
                pass
        m3 = re.search(r"return\s*==\s*\"([^\"]*)\"", post)
        if m3:
            if value != m3.group(1):
                return f"Postcondition failed: return expected '{m3.group(1)}', got {value}"

        # Numeric comparators: >=, <=, >, <, !=
        for op, sym in ((">=", ">="), ("<=", "<="), (">", ">"), ("<", "<"), ("!=", "!=")):
            m = re.search(rf"return\s*{re.escape(sym)}\s*(\d+(?:\.\d+)?)", post)
            if m:
                try:
                    bound = float(m.group(1)) if "." in m.group(1) else int(m.group(1))
                    try:
                        vnum = float(value) if isinstance(value, (int, float)) else None
                    except Exception:
                        vnum = None
                    if vnum is None:
                        return f"Postcondition failed: return is not numeric for comparator {sym} {bound}"
                    ok = {
                        ">=": vnum >= bound,
                        "<=": vnum <= bound,
                        ">": vnum > bound,
                        "<": vnum < bound,
                        "!=": vnum != bound,
                    }[sym]
                    if not ok:
                        return f"Postcondition failed: {vnum} {sym} {bound}"
                except Exception:
                    pass

        # where clauses with simple predicates
        if isinstance(value, (list, tuple)):
            parts = post.split('where')
            if len(parts) > 1:
                cond = parts[1]
                # Check sorted by ?.field asc|desc
                msort = re.search(r"sorted\s+by\s+\?\.([A-Za-z_][A-Za-z0-9_]*)\s+(asc|desc)", cond)
                if msort:
                    field, order = msort.group(1), msort.group(2)
                    for i in range(len(value)-1):
                        a = getattr(value[i], field, None) if hasattr(value[i], field) else value[i].get(field) if isinstance(value[i], dict) else None
                        b = getattr(value[i+1], field, None) if hasattr(value[i+1], field) else value[i+1].get(field) if isinstance(value[i+1], dict) else None
                        if a is None or b is None:
                            continue
                        if order == 'asc' and not (a <= b):
                            return f"Postcondition failed: not sorted ascending by {field}"
                        if order == 'desc' and not (a >= b):
                            return f"Postcondition failed: not sorted descending by {field}"
                # Check element predicate like ?.is_active==true
                preds = re.split(r"\s+AND\s+", cond)
                for pr in preds:
                    pr = pr.strip()
                    if pr.startswith('sorted '):
                        continue
                    # Handle ?.field==true/false
                    mbool = re.match(r"\?\.([A-Za-z_][A-Za-z0-9_]*)\s*==\s*(true|false)", pr)
                    if mbool:
                        fld = mbool.group(1)
                        want = (mbool.group(2) == 'true')
                        for el in value:
                            val = getattr(el, fld, None) if hasattr(el, fld) else el.get(fld) if isinstance(el, dict) else None
                            if bool(val) != want:
                                return f"Postcondition failed: element {fld} != {want}"
        return None
