"""카탈로그 로딩. 패키지 동봉본을 먼저 본다."""
from __future__ import annotations

import json
import os
import re
from collections.abc import Iterator
from pathlib import Path

_SEARCH = [
    Path(__file__).resolve().parent / "data",              # 패키지 동봉본
    Path(__file__).resolve().parents[2] / "catalog",       # 개발 중 원천
]


def _find(name: str) -> Path | None:
    override = os.getenv("MERITZ_CATALOG")
    if override:
        p = Path(override)
        if p.is_dir():
            p = p / name
        return p if p.is_file() else None
    for base in _SEARCH:
        p = base / name
        if p.is_file():
            return p
    return None


# 경로만으로 상태변경이 확실한 것 — 메서드를 믿지 않는다
_ACTION_PATH = re.compile(
    r"^/(?:trading|forex)/v\d+/"
    r"(?:"
    r"(?:overseas/)?(?:credit-)?(?:reserved-)?orders/(?:buy|sell|modify|cancel)"
    r"|exchanges"
    r")$"
)


class Api(dict):
    """카탈로그 항목. 자주 쓰는 것만 속성으로 꺼내 둔다."""

    @property
    def key(self) -> str:            return self["key"]
    @property
    def name(self) -> str:           return self["name"]
    @property
    def path(self) -> str:           return self["path"]
    @property
    def method(self) -> str:         return self["method"]
    @property
    def is_websocket(self) -> bool:  return self["protocol"] == "WEBSOCKET"
    @property
    def is_state_changing(self) -> bool:
        """경로와 메서드를 둘 다 본다. 하나가 틀려도 다른 하나가 막는다.

        경로는 그 요청이 무엇을 하는지 확정한다. 메서드가 잘못 등록돼도
        경로가 막는다.
        """
        if self.is_websocket:
            return False
        # 인증 계열(POST /oauth2/*)은 주문·환전이 아니다. 여기서 걸러 두지 않으면
        # 검색이 "행위어가 없다" 며 토큰 발급·폐기를 결과에서 통째로 빼 버린다.
        if self.get("category") == "oauth2":
            return False
        if _ACTION_PATH.match((self["path"] or "").rstrip("/")):
            return True
        return (self["method"] or "").upper() == "POST"

    @property
    def params(self) -> list[dict]:
        return self.get("request", {}).get("params", [])

    @property
    def response_fields(self) -> list[dict]:
        return self.get("response", {}).get("body", [])

    @property
    def required(self) -> list[dict]:
        return [p for p in self.params if p.get("required")]

    @property
    def optional(self) -> list[dict]:
        return [p for p in self.params if not p.get("required")]

    @property
    def example_request(self) -> str:
        return (self.get("example") or {}).get("request") or ""

    @property
    def example_response(self) -> str:
        return (self.get("example") or {}).get("response") or ""


class Catalog:
    def __init__(self, data: dict, corrections: dict | None = None):
        self.data = data
        self.corrections = corrections or {}
        self._by_key: dict[str, Api] = {}
        for a in data["apis"]:
            if a["key"] in self._by_key:
                raise ValueError(f"카탈로그에 api_type 이 중복됩니다: {a['key']}")
            self._by_key[a["key"]] = Api(a)
        self._fix: dict[str, list[dict]] = {}
        for c in (self.corrections.get("corrections") or []):
            for k in c.get("keys", []):
                self._fix.setdefault(k, []).append(c)

    def __len__(self) -> int:                 return len(self._by_key)
    def __iter__(self) -> Iterator[Api]:      return iter(self._by_key.values())
    def __contains__(self, k: str) -> bool:   return k in self._by_key
    def get(self, k: str) -> Api | None:      return self._by_key.get(k)
    def keys(self) -> list[str]:              return list(self._by_key)

    def rest(self) -> list[Api]:              return [a for a in self if not a.is_websocket]
    def websockets(self) -> list[Api]:        return [a for a in self if a.is_websocket]

    def corrections_for(self, key: str) -> list[dict]:
        """포털 등록분이 실호출과 다른 지점. 예시를 그대로 쓰면 당하는 것들이다."""
        return self._fix.get(key, [])

    @property
    def source(self) -> str:     return self.data.get("source", "")
    @property
    def generated(self) -> str:  return self.data.get("generated", "")
    @property
    def counts(self) -> dict:    return self.data.get("counts", {})


def load_catalog() -> Catalog:
    p = _find("catalog.json")
    if not p:
        raise FileNotFoundError(
            "catalog.json 을 찾을 수 없습니다.\n"
            "  설치가 온전한지 확인하거나, MERITZ_CATALOG 로 경로를 직접 지정하세요.")

    def side(name):
        f = p.parent / name
        return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else None

    return Catalog(json.loads(p.read_text(encoding="utf-8")),
                   side("corrections.json"))
