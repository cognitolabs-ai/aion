from pathlib import Path


def test_demo_ir_contains_ops():
    # Lazy import to avoid requiring Python CLI to exist in PATH
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("aion_demo", str(Path('scripts/aion_demo.py').resolve()))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    ir = mod.emit_mlir(mod.parse_aion(Path('examples/data_filter.aion')))
    assert 'aion.intent' in ir
    assert 'aion.pipe' in ir
    assert '| @filter' in ir
