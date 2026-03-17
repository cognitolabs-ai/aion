from pathlib import Path

import importlib


def test_non_null_filter_verify():
    aion = importlib.import_module('aionpy')
    u = aion.load_unit(Path('examples/non_null_filter.aion'))
    aion.Engine(u).run_verify()

