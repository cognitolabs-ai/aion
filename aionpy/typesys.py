from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class StructDef:
    name: str
    fields: Dict[str, str]


class TypeRegistry:
    def __init__(self) -> None:
        self.structs: Dict[str, StructDef] = {}

    def register_struct(self, name: str, fields: Dict[str, str]) -> None:
        self.structs[name] = StructDef(name, dict(fields))

    def has_struct(self, name: str) -> bool:
        return name in self.structs

    def validate_struct(self, name: str, obj: Dict) -> None:
        if name not in self.structs:
            raise ValueError(f"unknown struct type: {name}")
        sd = self.structs[name]
        # All declared fields must be present
        for f in sd.fields:
            if f not in obj:
                raise ValueError(f"missing field '{f}' in struct '{name}'")
        # No extra fields (conservative)
        for k in obj.keys():
            if k not in sd.fields:
                raise ValueError(f"unknown field '{k}' for struct '{name}'")

    def load_file(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8")
        # Very simple parser: struct Name { a: Type, b: Type }
        tok = re.compile(r"struct\s+([A-Za-z_][A-Za-z0-9_]*)\s*\{([^}]*)\}")
        for m in tok.finditer(text):
            name = m.group(1)
            body = m.group(2)
            fields: Dict[str, str] = {}
            for part in body.split(','):
                part = part.strip()
                if not part:
                    continue
                if ':' not in part:
                    continue
                fname, ftype = part.split(':', 1)
                fields[fname.strip()] = ftype.strip()
            if fields:
                self.register_struct(name, fields)


REGISTRY = TypeRegistry()


def load_standard_types(root: Optional[Path] = None) -> None:
    # Load from types/standard.aiont if present
    base = root or Path.cwd()
    p = base / 'types' / 'standard.aiont'
    if p.exists():
        REGISTRY.load_file(p)

