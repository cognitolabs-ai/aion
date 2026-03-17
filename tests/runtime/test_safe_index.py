from pathlib import Path

import importlib


def test_get_safe_first_verify():
    aion = importlib.import_module('aionpy')
    u = aion.load_unit(Path('examples/get_safe_first.aion'))
    aion.Engine(u).run_verify()

