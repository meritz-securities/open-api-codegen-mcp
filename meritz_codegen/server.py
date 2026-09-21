"""메리츠증권 Open API 코드 생성 MCP.

API 를 찾아 **바로 쓸 수 있는 Python 코드**를 만들어 준다. 실제 호출은 하지 않는다 —
호출은 `open-api-mcp` 가 한다.

명세는 **포털 등록분**을 그대로 쓴다. 다만 포털 예시가 실제와 다른 지점이 있어
(요청 예시에 필수 파라미터 누락 등), 그런 API 는 **되는 값으로 코드를 만들고**
머리말에 무엇이 다른지 적는다.

도구
  list_categories()                  분류와 건수
  search_api(keyword, category)      자연어 검색 (한글 별칭)
  get_api_detail(api_type)           경로·파라미터·응답 필드·주의사항
  generate_code(api_type)            호출 코드 (REST·실시간)
  api_conventions()                  인증·호출 규약·응답 코드·알려진 문제

실행
  uv run python server.py                             # stdio
  MCP_TYPE=streamable-http uv run python server.py     # HTTP /mcp
"""
from __future__ import annotations

import os
from collections import Counter

from fastmcp import FastMCP

from . import build_rest, build_token, build_websocket, load_catalog
from .search import CATEGORY_KO, search

CATALOG = load_catalog()
READ_ONLY = {"readOnlyHint": True, "destructiveHint": False,
             "idempotentHint": True, "openWorldHint": False}

mcp = FastMCP(
    name="Meritz Open API Codegen",
    instructions=(
        "메리츠증권 Open API 코드 생성 MCP 입니다. "
        "search_api 로 원하는 기능을 찾고, get_api_detail 로 파라미터를 확인한 뒤, "
        "generate_code 로 Python 코드를 받으세요. "
        "호출 규약과 알려진 문제는 api_conventions 에 있습니다. "
        "이 서버는 코드만 만들고 실제 호출은 하지 않습니다. "
        "주문·환전 코드를 만들 때는 실제로 체결될 수 있음을 사용자에게 알리세요."
    ),
    version="0.3.0",
)


@mcp.tool(description="분류와 API 개수를 반환합니다.", annotations=READ_ONLY)
def list_categories() -> dict:
    c = Counter(a["category"] for a in CATALOG)
    return {
        "total": len(CATALOG), **CATALOG.counts,
        "categories": [{"category": k, "name_ko": CATEGORY_KO.get(k, k), "count": v}
                       for k, v in sorted(c.items())],
        "source": CATALOG.source, "generated": CATALOG.generated,
    }


@mcp.tool(
    description=("자연어로 API 를 찾습니다. 예: search_api('삼성전자 현재가'), "
                 "search_api('매수'), search_api('실시간 체결통보'). "
                 "category 로 좁힐 수 있습니다 (account·domestic_market·"
                 "overseas_market·trading·forex·reference·realtime·oauth2). "
                 "인증(접근토큰 발급·폐기)은 '토큰'·'인증'·'oauth'·'revoke' 로 찾습니다."),
    annotations=READ_ONLY,
)
def search_api(keyword: str, category: str | None = None) -> dict:
    hits = search(CATALOG, keyword, category)
    return {"keyword": keyword, "category": category,
            "count": len(hits), "results": hits}


@mcp.tool(description="api_type 의 상세를 반환합니다 — 경로·파라미터·응답 필드·주의사항.",
          annotations=READ_ONLY)
def get_api_detail(api_type: str) -> dict:
    api = CATALOG.get(api_type)
    if not api:
        return {"error": f"알 수 없는 api_type: {api_type}",
                "hint": "search_api 로 먼저 찾으세요."}
    out = {
        "api_type": api.key, "name": api.name, "category": api["category"],
        "category_ko": CATEGORY_KO.get(api["category"], ""),
        "protocol": api["protocol"], "method": api.method, "api_path": api.path,
        "tr_id": api["tr_id"], "tps": api.get("tps"),
        "domain": api["domain"], "description": api.get("description"),
        "params": api.params,
        "response_fields": api.response_fields,
        "example_request": api.example_request,
        "example_response": api.example_response,
    }
    if api.is_websocket:
        out["subscribe"] = api.get("subscribe")
        out["note"] = ("접속점은 하나입니다. 무엇을 받을지는 구독 메시지의 tr_cd 가 정합니다. "
                       "API 마다 경로가 나뉘지 않습니다.")
    if api.is_state_changing:
        out["state_changing"] = True
        out["caution"] = "실제 주문·환전이 나갑니다."
    fixes = CATALOG.corrections_for(api.key)
    if fixes:
        out["portal_issues"] = fixes
        out["caution_portal"] = ("포털 등록분에 문제가 있습니다. 예시를 그대로 쓰지 마세요. "
                                 "generate_code 는 되는 값으로 만들어 줍니다.")
    return out


@mcp.tool(
    description=("api_type 을 호출하는 Python 코드를 만듭니다. "
                 "REST 는 토큰 발급·요청·응답 판정까지, 실시간은 웹소켓 구독 코드를 만듭니다. "
                 "주문·환전은 confirm=True 전까지 전송하지 않는 안전장치가 들어갑니다. "
                 "api_type='token' 이면 토큰 발급 코드만 만듭니다."),
    annotations=READ_ONLY,
)
def generate_code(api_type: str) -> dict:
    if api_type in ("token", "auth", "oauth"):
        return {"api_type": "token", "name": "접근토큰 발급", "language": "python",
                "code": build_token(), "requires": ["requests"],
                "env": ["MERITZ_APP_KEY", "MERITZ_APP_SECRET"],
                # token.py 로 저장하면 표준 라이브러리 token 모듈을 가려
                # 같은 폴더의 다른 파일이 전부 깨진다.
                "filename": "meritz_token.py"}
    api = CATALOG.get(api_type)
    if not api:
        return {"error": f"알 수 없는 api_type: {api_type}",
                "hint": "search_api 로 먼저 찾으세요."}

    code = build_websocket(api, CATALOG) if api.is_websocket else build_rest(api, CATALOG)
    out = {"api_type": api.key, "name": api.name, "language": "python",
           "protocol": api["protocol"], "code": code,
           "requires": ["websockets", "requests"] if api.is_websocket else ["requests"],
           "env": ["MERITZ_APP_KEY", "MERITZ_APP_SECRET"],
           "filename": f"{api.key}.py"}
    if api.is_state_changing:
        out["caution"] = ("실제 주문·환전 코드입니다. confirm=True 를 넘겨야 전송됩니다. "
                          "먼저 confirm 없이 실행해 내용을 확인하고, 사용자에게 알린 뒤 진행하세요.")
    if api.is_websocket:
        out["note"] = "접속점은 하나이고 구독 메시지의 tr_cd 가 대상을 정합니다."
    if CATALOG.corrections_for(api.key):
        out["portal_issue_handled"] = ("포털 예시가 실제와 달라, 되는 값으로 만들었습니다. "
                                       "코드 머리말에 차이를 적어 두었습니다.")
    return out


@mcp.tool(description="인증 절차·호출 규약·응답 코드·알려진 문제를 반환합니다.",
          annotations=READ_ONLY)
def api_conventions() -> dict:
    return {
        "auth": {
            "path": "/oauth2/token",
            "content_type": "application/x-www-form-urlencoded",
            "body": "grant_type=client_credentials&client_id=<앱키>"
                    "&client_secret=<시크릿>&scope=login",
            "note": "JSON 으로 보내면 EGW00116 으로 거절됩니다. 반드시 form-urlencoded.",
            "use": "authorization: Bearer <access_token>",
            "expires": "12시간. 만료 전까지 재사용하세요.",
        },
        "domain": {
            "rest": "https://openapi.imeritz.com:9443",
            "websocket": "wss://openapi.imeritz.com:29443/websocket",
        },
        "call": {
            "method": "GET(조회) / POST(주문·환전) — 행위가 경로로 갈립니다",
            "get": "파라미터는 쿼리스트링",
            "post": "파라미터는 JSON 본문 최상위. 전문 블록(InBlock1) 봉투를 쓰지 않습니다",
            "headers": ["authorization: Bearer <token>", "mac_address (필수)"],
            "response": "단건은 data 객체, 목록은 data 배열. rsp_cd·rsp_msg 는 최상위",
            "paging": 'rsp_cd 가 "5762" 면 tr_cont·tr_cont_key 로 이어서 조회',
        },
        "websocket": {
            "endpoint": "wss://openapi.imeritz.com:29443/websocket",
            "note": "접속점은 하나입니다. 무엇을 받을지는 구독 메시지의 tr_cd 가 정합니다.",
            "subscribe": '{"header":{"token":"Bearer <token>","tr_type":"1"},'
                         '"body":{"tr_cd":"<코드>","tr_key":"<종목>"}}',
            "unsubscribe": '같은 메시지에서 tr_type 을 "2" 로',
            "ack": '구독 응답에는 header.rsp_cd 가 있습니다(정상 "00000"). 데이터에는 없습니다',
            "error": '오류는 봉투 없이 최상위 {"rsp_cd":…,"rsp_msg":…} 로 옵니다',
        },
        "result_codes": {
            "0000": "정상 처리",
            "0001": "주문 접수 — 접수 성공일 뿐 체결·수리 확정이 아닙니다",
            "5762": "조회가 계속됩니다 (연속 조회)",
            "5766": "조회 완료", "5820": "조회할 내역 없음",
            "5822": "조회할 내역 없음 — 오류가 아닙니다",
            "00000": "실시간 구독 정상 (웹소켓은 5자리)",
            "WSC00106": "허용되지 않는 tr_cd", "WSC00108": "tr_key 확인",
            "EGW00121": "유효하지 않은 token",
            "EGW00202": 'authorization 에 "Bearer " 접두어 누락',
            "IGW50004": "게이트웨이 오류 — 필수 파라미터 누락일 때 자주 납니다",
            "IGW50024": "mac_address 헤더 누락",
        },
        "known_issues": CATALOG.corrections.get("corrections", []),
        "source": CATALOG.source,
    }


@mcp.prompt(name="meritz_code_prompt",
            description="작업 설명만 넣으면 검색→상세→코드 생성 흐름을 안내합니다.")
def meritz_code_prompt(task: str, iscd: str = "") -> str:
    lines = [f"메리츠 Open API 로 다음을 하려 합니다: {task}", "",
             "아래 순서로 진행해 주세요.",
             "1. api_conventions() 로 인증·호출 규약과 알려진 문제를 확인합니다.",
             f"2. search_api('{task}') 로 알맞은 API 를 찾습니다.",
             "3. get_api_detail(api_type) 로 파라미터를 확인합니다.",
             "4. generate_code(api_type) 로 코드를 받습니다."]
    if iscd:
        lines += ["", f"종목코드는 {iscd} 입니다.",
                  "  국내 시세  6자리        005930",
                  "  국내 주문  'A' + 6자리   A005930",
                  "  해외       심볼 대문자    AAPL",
                  "  해외 실시간 <거래소>@<종목>  OQ@NVDA"]
    lines += ["", "주의 — 결과가 주문·환전 API 라면 실제로 체결될 수 있습니다. "
                  "생성 코드는 confirm=True 전까지 보내지 않으니, 먼저 내용을 확인하고 "
                  "사용자에게 알린 뒤 진행하세요."]
    return "\n".join(lines)


def main() -> None:
    mode = os.getenv("MCP_TYPE", "stdio")
    if mode == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=mode, host=os.getenv("MCP_HOST", "127.0.0.1"),
                port=int(os.getenv("MCP_PORT", "8000")),
                path=os.getenv("MCP_PATH", "/mcp"))


if __name__ == "__main__":
    main()
