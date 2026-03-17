from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .dot import DotDict, wrap


class APIError(Exception):
    pass


@dataclass
class Response:
    status: int
    body: str | None = None
    headers: Dict[str, str] | None = None

    def json(self) -> Any:
        if not self.body:
            return None
        try:
            return wrap(json.loads(self.body))
        except Exception:
            return None

    def text(self) -> str:
        return self.body or ""


class HTTPClient:
    def __init__(self) -> None:
        self._mocks: Dict[str, Response] = {}

    def mock(self, url: str, resp: Response) -> None:
        self._mocks[url] = resp

    def get(self, url: str, options: Optional[Dict[str, Any]] = None) -> Response:
        if url in self._mocks:
            return self._mocks[url]
        return Response(500, None)


http = HTTPClient()

