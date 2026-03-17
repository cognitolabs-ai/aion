from pathlib import Path

import importlib


def test_group_by_window_verify():
    aion = importlib.import_module('aionpy')
    u = aion.load_unit(Path('examples/group_by_window.aion'))
    aion.Engine(u).run_verify()

