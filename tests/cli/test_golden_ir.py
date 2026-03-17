from pathlib import Path


def _normalize(s: str) -> str:
    # drop multiple spaces and trim lines; ignore trailing spaces
    norm = []
    for line in s.splitlines():
        line = ' '.join(line.strip().split())
        if line:
            norm.append(line)
    return '\n'.join(norm).strip()


def test_golden_data_filter_ir():
    import importlib.util
    spec = importlib.util.spec_from_file_location("aion_demo", str(Path('scripts/aion_demo.py').resolve()))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    # Generate IR
    ir = mod.emit_mlir(mod.parse_aion(Path('examples/data_filter.aion')))
    # Compare to golden
    golden = Path('tests/cli/golden/data_filter.mlir').read_text(encoding='utf-8')
    assert _normalize(ir) == _normalize(golden)

