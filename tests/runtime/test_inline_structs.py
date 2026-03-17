from pathlib import Path

import importlib


def test_inline_structs_verify():
    aion = importlib.import_module('aionpy')
    u = aion.load_unit(Path('examples/inline_structs.aion'))
    aion.Engine(u).run_verify()

