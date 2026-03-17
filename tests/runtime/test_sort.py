from pathlib import Path

import importlib


def test_sort_products_verify():
    aion = importlib.import_module('aionpy')
    u = aion.load_unit(Path('examples/sort_products.aion'))
    aion.Engine(u).run_verify()

