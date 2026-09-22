"""메리츠 Open API 코드 생성.

명세와 API별 응답 처리 참고자료를 기준으로 호출 코드를 생성한다.
응답 처리에 필요한 주의사항은 `corrections.json` 으로 관리한다.
"""
from .catalog import Catalog, load_catalog
from .python import build_rest, build_token, build_websocket

__all__ = ["Catalog", "load_catalog", "build_rest", "build_token", "build_websocket"]
