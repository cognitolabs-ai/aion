from __future__ import annotations

from typing import Any, Iterable, Iterator


class DotDict(dict):
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as e:
            raise AttributeError(name) from e

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


class DotList(list):
    def len(self) -> int:
        return len(self)

    def push(self, item: Any) -> None:
        self.append(item)

    def pop(self) -> Any:  # type: ignore[override]
        if not self:
            return None
        return super().pop()

    def get(self, index: int) -> Any:
        if index < 0 or index >= len(self):
            return None
        return self[index]

    # iteration helpers for type-checkers
    def __iter__(self) -> Iterator[Any]:  # type: ignore[override]
        return super().__iter__()


def wrap(value: Any) -> Any:
    """Recursively wrap dicts/lists for attribute-like access and stdlib methods."""
    if isinstance(value, list):
        return DotList([wrap(v) for v in value])
    if isinstance(value, dict):
        return DotDict({k: wrap(v) for k, v in value.items()})
    return value

