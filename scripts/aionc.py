#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from aionpy.engine import Engine, load_unit
from aionpy.checker import TypeChecker, TypeCheckError
from aionpy.nullflow import NullFlowChecker, NullFlowError


def main() -> None:
    ap = argparse.ArgumentParser(description="Aion reference interpreter (subset)")
    ap.add_argument("source", type=Path, help="Path to .aion source file")
    ap.add_argument("--run", choices=["verify", "call"], default="verify")
    ap.add_argument("--args", help="Python literal list of positional args for call mode", default=None)
    args = ap.parse_args()

    unit = load_unit(args.source)
    # Run static checks first
    TypeChecker(unit).run()
    NullFlowChecker(unit).run()
    engine = Engine(unit)
    if args.run == "verify":
        engine.run_verify()
        print("verify: PASS")
    else:
        import ast, json
        call_args = []
        if args.args:
            call_args = ast.literal_eval(args.args)
            if not isinstance(call_args, list):
                raise SystemExit("--args must be a Python list, e.g., --args '[1,2]' ")
        # Provide a conversion from Dot structures to plain JSON
        def to_plain(x):
            from aionpy.dot import DotDict, DotList
            if isinstance(x, DotList) or isinstance(x, list):
                return [to_plain(v) for v in list(x)]
            if isinstance(x, DotDict) or isinstance(x, dict):
                return {k: to_plain(v) for k, v in dict(x).items()}
            return x
        fn = unit.name
        res = engine.env.get(fn)
        if res is None:
            # ensure proxy is installed by preparing verify env once
            engine.run_verify()
        res = engine.env[fn](*call_args)
        print(json.dumps(to_plain(res)))


if __name__ == "__main__":
    main()
