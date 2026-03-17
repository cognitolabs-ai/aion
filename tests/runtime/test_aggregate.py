from pathlib import Path

import importlib


def test_sum_active_prices():
    aion = importlib.import_module('aionpy')
    u = aion.load_unit(Path('examples/aggregate.aion'))
    aion.Engine(u).run_verify()

