from pathlib import Path

import importlib


def test_fetch_user_profile_verify():
    aion = importlib.import_module('aionpy')
    u = aion.load_unit(Path('examples/network_call.aion'))
    aion.Engine(u).run_verify()

