"""메리츠 Open API 코드 생성.

명세는 **포털 등록분**을 그대로 쓴다. 저장소가 포털과 다르면 이용자가 혼란스럽다.
포털 예시가 실제와 다른 지점은 `corrections.json` 으로 따로 알려 준다.
"""
from .catalog import Catalog, load_catalog
from .python import build_rest, build_token, build_websocket

__all__ = ["Catalog", "load_catalog", "build_rest", "build_token", "build_websocket"]
