from pathlib import Path

import importlib


def test_process_metrics_verify():
    aion = importlib.import_module('aionpy')
    u = aion.load_unit(Path('examples/process_metrics.aion'))
    aion.Engine(u).run_verify()

