"""메리츠증권 Open API 코드 생성 MCP.

API 를 찾아 **바로 쓸 수 있는 Python 코드**를 만들어 준다. 실제 호출은 하지 않는다 —
호출은 `open-api-mcp` 가 한다.

명세와 응답 처리 참고자료를 기준으로 API 호출 코드를 생성한다. API별 응답
처리상 주의사항이 있는 경우 생성된 코드에 해당 내용을 함께 표시한다.

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
# from __future__ import annotations 를 쓰지 않는다.
# 그것이 있으면 어노테이션이 전부 문자열이 되고, FastMCP 는 프롬프트 인자의
# 타입이 str 이 아니라고 판단해 설명 뒤에 JSON 스키마를 덧붙인다. 그 문구가
# 입력 대화상자에 그대로 보인다. 이 패키지는 3.11 이상이라 str | None 같은
# 표기가 런타임에 그대로 동작하므로 future import 가 필요 없다.

import os
from collections import Counter
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from . import __version__, build_rest, build_token, build_websocket, load_catalog
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
    version=__version__,
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
def search_api(
    keyword: Annotated[str, Field(description=(
        "찾으려는 것을 우리말로 적습니다. 예: '삼성전자 현재가', '매수 주문', "
        "'실시간 체결통보', '예수금'. API 이름을 몰라도 됩니다."))],
    category: Annotated[str | None, Field(description=(
        "분류로 좁히고 싶을 때만 씁니다. account·domestic_market·overseas_market·"
        "trading·forex·reference·realtime·oauth2 중 하나."))] = None,
) -> dict:
    hits = search(CATALOG, keyword, category)
    return {"keyword": keyword, "category": category,
            "count": len(hits), "results": hits}


@mcp.tool(description="api_type 의 상세를 반환합니다 — 경로·파라미터·응답 필드·주의사항.",
          annotations=READ_ONLY)
def get_api_detail(
    api_type: Annotated[str, Field(description=(
        "search_api 결과의 api_type 값을 그대로 넣습니다. 예: 'market_prices', "
        "'order_buy'. 짐작해서 쓰지 말고 먼저 search_api 로 찾으십시오."))],
) -> dict:
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
        out["response_handling_notes"] = fixes
        out["caution_response"] = ("이 API에는 별도의 응답 처리 참고사항이 있습니다. "
                                   "생성된 코드의 주석을 확인하십시오.")
    return out


@mcp.tool(
    description=("api_type 을 호출하는 Python 코드를 만듭니다. "
                 "REST 는 토큰 발급·요청·응답 판정까지, 실시간은 웹소켓 구독 코드를 만듭니다. "
                 "주문·환전은 confirm=True 전까지 전송하지 않는 안전장치가 들어갑니다. "
                 "api_type='token' 이면 토큰 발급 코드만 만듭니다."),
    annotations=READ_ONLY,
)
def generate_code(
    api_type: Annotated[str, Field(description=(
        "코드를 만들 API 의 api_type. search_api 나 get_api_detail 에서 확인한 값을 "
        "넣습니다. 'token' 이면 접근토큰 발급 코드만 만듭니다."))],
) -> dict:
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
        out["response_handling_note"] = ("이 API에는 별도의 응답 처리 참고사항이 있습니다. "
                                          "생성된 코드의 주석을 확인하십시오.")
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
    """작업 설명만 넣으면 검색→상세→코드 생성 흐름을 안내합니다.

    인자 설명을 Annotated·Field 가 아니라 이 docstring 에 두는 이유가 있다.
    FastMCP 는 프롬프트 인자의 타입이 str 이 아니면 설명 뒤에 JSON 스키마를
    덧붙인다. Annotated[str, Field(...)] 는 str 이 아니라서 걸리고, 그러면
    입력 대화상자에 유니코드로 이스케이프된 스키마가 그대로 보인다.

    Args:
        task: 무엇을 하고 싶은지 한 줄로 적습니다. 예) 삼성전자 현재가를 조회하고 싶다 /
            보유 종목의 평가금액을 받고 싶다 / 지정가 매수 주문을 내고 싶다
        iscd: 종목이 정해져 있으면 넣습니다. 비워 두셔도 됩니다.
            국내 시세는 6자리(005930), 국내 주문은 A+6자리(A005930),
            해외는 대문자 심볼(AAPL)
    """
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
