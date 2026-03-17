from pathlib import Path

import importlib
import pytest


def test_requires_match_after_get():
    aion = importlib.import_module('aionpy')
    u = aion.load_unit(Path('examples/unsafe_get.aion'))
    with pytest.raises(Exception):
        aion.Engine(u).run_verify()

