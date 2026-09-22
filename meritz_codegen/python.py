"""Python 호출 코드 생성.

생성물은 **그대로 복사해 붙이면 도는 코드**여야 한다. 컴파일만 되는 것으로는 부족하다.
토큰 재사용·오류 처리·응답 판정·연속조회·주문 확인이 들어간다.

API별 응답 처리 참고자료를 반영해 호출 코드를 만든다.
"""
from __future__ import annotations

import json
import keyword
import re
from typing import Any

PROD = "https://openapi.imeritz.com:9443"
PROD_WS = "wss://openapi.imeritz.com:29443/websocket"

# 성공으로 보는 응답 코드
# 5820·5822 는 "자료 없음" 이다. 오류가 아니다.
# 다만 **자료를 담고도 5820 이 온다**(담보 현황·실현손익 실측). 코드만 보고
# "자료 없음" 으로 판단하지 말고 data 를 보아야 한다.
OK_CODES = ("0000", "0001", "5762", "5766", "5820", "5822")
NO_DATA_CODES = ("5820", "5822")

# 주문 경고 코드. rsp_cd 가 0001("주문이 완료되었습니다")로 와도 이 값이면
# **접수되지 않은 것**이다. warn_msg 를 사용자에게 보이고 warn_cnfr_yn="A" 로
# 같은 요청을 다시 보내야 접수된다.
# 재전송(warn_cnfr_yn="A")으로 접수되는 값. 국내와 해외의 체계가 다르다.
# 명세가 "코드를 공용으로 쓰지 마십시오" 라고 명시한다.
RESEND_OK = {
    "domestic": ("1", "3", "4", "6", "7", "9", "a", "c", "d", "f", "g"),
    "overseas": ("1", "3"),
}


def safe_name(name: str) -> str:
    """파라미터명을 파이썬 인자명으로 바꾼다.

    예약어는 뒤에 _ 를 붙인다(from -> from_). 식별자가 될 수 없는 이름을 조용히
    넘기면 컴파일되지 않는 코드가 나가므로 여기서 막는다.
    """
    if not isinstance(name, str) or not name:
        raise ValueError("파라미터명이 비어 있습니다: %r" % (name,))
    if not name.isidentifier():
        raise ValueError(
            "파이썬 인자명으로 쓸 수 없는 파라미터명입니다: %r  "
            "카탈로그를 확인하세요. 이대로는 컴파일되지 않습니다." % (name,))
    return name + "_" if keyword.iskeyword(name) else name


_TAG = re.compile(r"<[^>]+>")
_TRIPLE = chr(34) * 3


def clean_text(t) -> str:
    """설명 문구를 docstring 에 넣을 수 있게 다듬는다.

    HTML 태그를 걷어내고, docstring 을 깨뜨리는 삼중따옴표와 제어문자를 없앤다.
    포털 문구는 사람이 편집하므로 무엇이 들어올지 모른다.
    """
    t = str(t or "").replace("<br/>", " ").replace("<br>", " ")
    t = _TAG.sub(" ", t).replace("&nbsp;", " ").replace("&amp;", "&")
    t = t.replace(_TRIPLE, chr(39) * 3).replace(chr(92), "/")
    t = "".join(ch if (ch.isprintable() or ch == " ") else " " for ch in t)
    return " ".join(t.split())


def _wrap(text: str, width: int = 92, indent: str = " " * 10) -> list:
    """자르지 않고 접는다. 잘라 버리면 코드값 표가 통째로 사라진다."""
    out, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            out.append(indent + line)
            line = word
        else:
            line = (line + " " + word).strip()
    if line:
        out.append(indent + line)
    return out


def _hint(p: dict) -> str:
    return "int" if p.get("type") == "number" else "str"


def example_values(api, catalog=None) -> dict:
    """실행 예시에 넣을 값.

    포털 요청 예시에서 뽑되, 그 예시가 틀린 API 는 corrections 의 값을 쓴다.
    설명 문구를 정규식으로 캐지 않는다. 틀린 값이 들어가면 빈 데이터를 부른다.
    """
    out: dict[str, Any] = {}
    ex = api.example_request

    # 포털 예시가 틀린 API 는 정정본을 먼저 본다
    if catalog is not None:
        for fx in catalog.corrections_for(api.key):
            we = fx.get("working_example")
            if we and ("?" in we or "=" in we):
                ex = we
                break

    head = ex.split("\n", 1)[0]
    if "?" in head:
        for pair in head.split("?", 1)[1].split("&"):
            if "=" in pair:
                k, v = pair.split("=", 1)
                out[k] = v

    # 폼인코딩 본문 — OAuth 는 JSON 이 아니라 k=v&k=v 로 보낸다.
    # 이 형태를 못 읽으면 포털에 예시가 멀쩡히 있는데도 "예시 없음" 이 된다.
    if (api.get("content_type") or "").startswith("application/x-www-form-urlencoded"):
        for line in ex.split("\n"):
            line = line.strip()
            if not line or ":" in line.split("=", 1)[0] or line.split(" ", 1)[0].isupper():
                continue
            if "=" in line:
                for pair in line.split("&"):
                    if "=" in pair:
                        k, v = pair.split("=", 1)
                        out[k.strip()] = v.strip()

    # POST 본문 — 헤더의 "Bearer {access_token}" 중괄호를 본문으로 오인하지 않도록
    # 빈 줄(헤더와 본문의 경계) 뒤에서 찾는다.
    blank = ex.find("\n\n")
    tail = ex[blank + 2:] if blank >= 0 else ""
    br = tail.find("{")
    if br >= 0:
        try:
            body = json.loads(tail[br:])
            if isinstance(body, dict):
                out.update({k: v for k, v in body.items()
                            if not isinstance(v, (dict, list))})
        except ValueError:
            pass

    # 주문·환전 예시는 눈에 띄게 작은 값으로 낮춘다.
    # 주석을 푸는 것만으로 큰 금액이 운영으로 나가지 않도록 한다.
    if api.is_state_changing:
        for k in list(out):
            if k in ("odqt", "rctf_qty", "cncl_qty"):
                out[k] = 1
            elif k in ("oder_unpr", "wncr_amt", "frcr_amt", "tr_amt",
                       "ovrs_stck_oder_prc"):
                out[k] = 1

    for p in api.params:                       # 타입 보정
        v = out.get(p["name"])
        if p.get("type") == "number" and isinstance(v, str) and v.lstrip("-").isdigit():
            out[p["name"]] = int(v)
    return out


# ── 공통 머리말 ────────────────────────────────────────────────────
_COMMON = '''from __future__ import annotations

import os
import time
import uuid
from typing import Any

import requests

BASE_URL = os.getenv("MERITZ_BASE_URL", "%s").rstrip("/")
APP_KEY = os.getenv("MERITZ_APP_KEY")
APP_SECRET = os.getenv("MERITZ_APP_SECRET")
TIMEOUT = 15

# 미리보기에 그대로 찍으면 안 되는 값. 앱키도 자격증명이다 — 계좌를 가리킨다.
_MASK = frozenset({"client_id", "client_secret", "app_key", "appkey",
                   "app_secret", "token", "access_token", "acnt_pwd"})

_token: dict[str, Any] = {"value": None, "expires_at": 0.0}


class MeritzError(RuntimeError):
    """호출 실패. 응답이 있으면 status·body 를 함께 담는다."""

    def __init__(self, message: str, *, status: int | None = None, body: Any = None):
        super().__init__(message)
        self.status = status
        self.body = body


def _mac_address() -> str:
    """게이트웨이 필수 헤더. 없으면 IGW50024 로 거절된다."""
    n = uuid.getnode()
    return "".join(f"{(n >> s) & 0xFF:02X}" for s in range(40, -1, -8))


def get_token() -> str:
    """접근토큰을 발급받아 만료 전까지 재사용한다.

    form-urlencoded 로 보내야 한다 — JSON 으로 보내면 EGW00116 으로 거절된다.
    """
    if _token["value"] and time.time() < _token["expires_at"]:
        return _token["value"]
    if not APP_KEY or not APP_SECRET:
        raise MeritzError("MERITZ_APP_KEY / MERITZ_APP_SECRET 환경변수가 필요합니다.")

    resp = requests.post(
        f"{BASE_URL}/oauth2/token",
        data={"grant_type": "client_credentials", "client_id": APP_KEY,
              "client_secret": APP_SECRET, "scope": "login"},
        headers={"content-type": "application/x-www-form-urlencoded"},
        timeout=TIMEOUT,
    )
    if resp.status_code != 200:
        # 게이트웨이는 무엇이 틀렸는지 알려준다 —
        #   403 {"rsp_cd":"EGW00103","rsp_msg":"유효하지 않은 client_id입니다."}
        # 그걸 버리면 앱키가 잘못된 것인지 알 수 없다.
        try:
            _e = resp.json()
        except ValueError:
            _e = {}
        _detail = " ".join(x for x in (_e.get("rsp_cd"), _e.get("rsp_msg"),
                                       _e.get("rsp_sub_msg")) if x) or resp.text[:200]
        raise MeritzError(
            f"토큰 발급 실패 (HTTP {resp.status_code}): {_detail} — "
            f"요청한 서버는 {BASE_URL} 입니다. 앱키와 시크릿을 확인하세요.",
            status=resp.status_code, body=resp.text)

    data = resp.json()
    _token["value"] = data["access_token"]
    _token["expires_at"] = time.time() + int(data.get("expires_in", 43200)) - 60
    return _token["value"]
''' % PROD


# 조회 결과가 진짜인지 확인할 식별 필드. 없는 종목을 넣으면 게이트웨이가
# 오류 대신 값이 채워진 껍데기를 돌려주므로, "값이 몇 개 있나" 로는 가릴 수 없다.
# 요청한 종목이 응답에 그대로 돌아오는지를 본다.
_ECHO_FIELDS = ("shrn_iscd", "iscd", "fidxr_iscd", "kor_isnm", "prpr", "stck_prpr")


_OAUTH_CHECK = '''

def check(status: int, body: Any) -> Any:
    """OAuth2 응답을 판정한다.

    인증 계열은 업무 API 와 응답 형태가 다르다 — rsp_cd 가 오지 않는다.
    발급은 access_token 이, 폐기는 code/message 가 온다. 그래서 rsp_cd 가
    없다고 실패로 보면 정상 응답을 전부 오류로 만든다.
    """
    if status != 200:
        _e = body if isinstance(body, dict) else {}
        _detail = " ".join(str(x) for x in (_e.get("rsp_cd"), _e.get("error"),
                                            _e.get("rsp_msg"), _e.get("message"))
                           if x) or str(body)[:200]
        raise MeritzError(f"HTTP {status}: {_detail}", status=status, body=body)
    if isinstance(body, dict):
        _code = body.get("code")
        if _code is not None and str(_code) not in ("200", "0", "0000"):
            raise MeritzError(f"{_code} — {body.get('message')}",
                              status=status, body=body)
    return body
'''


def _check_fn(degraded: bool, warns: bool = False, echo: bool = False) -> str:
    """응답 판정 함수.

    읽히는 오류 코드를 '손상' 으로 넘기면 거절된 주문이 성공으로 보인다.
    그래서 읽히는 코드는 성공 목록에 없으면 무조건 오류다.
    """
    body = ['', '', 'def check(status: int, body: Any) -> Any:',
            '    """응답을 판정한다. HTTP 200 만으로 성공을 단정하지 않는다."""',
            '    if status != 200:',
            '        raise MeritzError(f"HTTP {status}", status=status, body=body)',
            '    if not isinstance(body, dict):',
            '        return body',
            '']
    if warns:
        body += [
            '    # 경고 확인이 먼저다. rsp_cd 가 "0001"(주문이 완료되었습니다)로 와도',
            '    # warn_cls_code 가 경고 값이면 **접수되지 않은 상태**다.',
            '    _warned = _warning_row(body)',
            '    if _warned:',
            '        raise MeritzWarning(',
            '            (_warned[1] or "확인이 필요한 주문입니다")',
            '            + (\' — warn_cnfr_yn="A" 로 재전송하면 접수됩니다.\'',
            '               if _warned[2] else',
            '               " — 보류 상태라 재전송해도 접수되지 않습니다."),',
            '            code=_warned[0], body=body)',
            '']
    body += [
            '    code = body.get("rsp_cd")',
            '    readable = isinstance(code, str) and code.isprintable() and code.strip()',
            '    if readable:',
            f'        if code in {OK_CODES!r}:',
            ('            if code not in %r and _looks_empty(body.get("data")):\n'
             '                raise MeritzError("조회 결과가 비어 있습니다. "\n'
             '                                  "종목코드·조회조건을 확인하세요.",\n'
             '                                  status=status, body=body)' % (NO_DATA_CODES,)
             if echo else '            pass'),
            '            return body',
            '        # rsp_sub_msg 에 실제 조치 정보가 담긴다',
            '        #   0760 "권한이 없습니다." + "계좌 관리점과 직원소속부서 확인!!"',
            '        _sub = body.get("rsp_sub_msg")',
            '        raise MeritzError(f"업무 오류 {code} — {body.get(\'rsp_msg\')}"',
            '                          + (f" — {_sub}" if _sub else ""),',
            '                          status=status, body=body)']
    if degraded:
        body += [
            '',
            '    # 이 API 는 rsp_cd 를 신뢰할 수 없다. data 로 판정한다.',
            '    if _looks_empty(body.get("data")):',
            '        raise MeritzError("응답 코드를 읽을 수 없고 결과도 비어 있습니다. "',
            '                          "종목코드·조회조건을 확인하세요.", status=status, body=body)',
            '    print("[주의] 응답 코드가 손상돼 업무 성공 여부는 검증되지 않았습니다.")',
            '    return body']
    else:
        body += [
            '',
            '    raise MeritzError(f"응답 코드를 읽을 수 없습니다({code!r}).",',
            '                      status=status, body=body)']
    return "\n".join(body)


_EMPTY_FN = '''

def _looks_empty(data: Any) -> bool:
    """결과가 빈 껍데기인지 본다.

    없는 종목이나 빈 종목코드를 넣으면 게이트웨이가 오류 대신 값이 0/빈 문자열인
    응답을 돌려준다. 이때도 시장명 같은 필드는 채워져 오므로 "값이 몇 개 있나" 로는
    가릴 수 없다. 종목 식별자와 가격이 실제로 돌아왔는지를 본다.
    """
    if data is None:
        return True
    if isinstance(data, (list, tuple)):
        return len(data) == 0
    if not isinstance(data, dict):
        return False
    present = [data.get(k) for k in %r if k in data]
    if present:
        return not any(v not in (None, "", 0, "0", "0.0000") for v in present)
    return not any(v not in (None, "", 0, "0", [], {}) for v in data.values())
''' % (_ECHO_FIELDS,)


_WARN_CLASS = '''
_RESEND_OK = frozenset(%r)   # 이 값이면 warn_cnfr_yn="A" 로 재전송하면 접수된다



def _warning_row(body):
    """접수되지 않은 주문이면 (코드, 사유, 재전송으로 풀리는가). 아니면 None.

    "0" 이 아니면 접수되지 않은 것이다. 국내와 해외는 코드 체계가 달라
    재전송으로 풀리는 값만 나눠 둔다.

    응답이 단건 dict 일 수도 배열일 수도 있고, 최상위에 올 수도 있다.
    """
    if not isinstance(body, dict):
        return None
    data = body.get("data")
    rows = data if isinstance(data, list) else ([data] if isinstance(data, dict) else [])
    for row in list(rows) + [body]:
        if not isinstance(row, dict) or "warn_cls_code" not in row:
            continue
        code = str(row.get("warn_cls_code", "")).strip()
        if code and code != "0":
            return code, str(row.get("warn_msg") or "").strip(), code in _RESEND_OK
    return None


class MeritzWarning(MeritzError):
    """주문에 경고가 붙어 **접수되지 않은** 상태.

    rsp_cd 가 "0001"(주문이 완료되었습니다)로 와도 warn_cls_code 가 경고 값이면
    접수된 것이 아니다. warn_msg 를 사용자에게 보이고 동의를 받은 뒤,
    같은 요청을 warn_cnfr_yn="A" 로 다시 보내야 접수된다.
    """

    def __init__(self, message: str, *, code: str | None = None, body: Any = None):
        super().__init__(message, body=body)
        self.warn_cls_code = code
'''


def _param_doc(api) -> list[str]:
    if not api.params:
        return []
    out = ["", "    파라미터"]
    for p in api.params:
        nm = safe_name(p["name"])
        alias = ' (요청 키 "%s")' % p["name"] if nm != p["name"] else ""
        mark = "필수" if p.get("required") else "선택"
        out.append("      %-24s %s  %s%s" % (nm, mark, clean_text(p.get("name_ko")), alias))
        d = clean_text(p.get("description"))
        if d:
            out += _wrap(d)
    return out


def _warnings(api, catalog) -> list[str]:
    """API별 응답 처리 참고사항을 코드 머리말에 적는다."""
    if catalog is None:
        return []
    out = []
    for fx in catalog.corrections_for(api.key):
        out += ["", f"주의 — 이 API의 응답 처리 참고사항: {clean_text(fx['kind'])}"]
        if fx.get("if_you_follow_the_portal"):
            out.append(f"  일반적인 처리 방식으로 호출하면: {clean_text(fx['if_you_follow_the_portal'])}")
        if fx.get("working_example"):
            out.append(f"  실제로 되는 값: {clean_text(fx['working_example'])}")
        if fx.get("actual_parameter"):
            out.append(f"  실제 파라미터명: {clean_text(fx['actual_parameter'])}")
        out.append("  이 코드는 되는 쪽으로 만들어져 있습니다.")
    return out


def _args_prefix(call: list) -> str:
    """실행 예시 인자를 이어 쓸 접두어. 인자가 없으면 앞 쉼표를 두지 않는다.

    앞 쉼표가 남으면 주석을 풀었을 때 SyntaxError 가 난다 —
    풀어 쓰라고 넣은 주석이 안 돌아가면 없느니만 못하다.
    """
    base = ", ".join(c for c in call if not c.startswith("confirm"))
    return f"{base}, " if base else ""


# 포털 예시에 그대로 적힌 자리표시자. 값을 베껴 넣으면 EGW00103 이 난다.
# 실행 예시에서는 코드 안의 환경변수·함수로 바꿔 둔다.
_PLACEHOLDERS = {
    "{app_key}": "APP_KEY",
    "{app_secret}": "APP_SECRET",
    "{access_token}": "get_token()",
}


def build_rest(api, catalog=None) -> str:
    fn = api.key
    is_post = api.method == "POST"
    # 본문 형식은 카탈로그의 content_type 이 정한다. api_type 으로 가르지 않는다 —
    # 폼인코딩 API 를 JSON 으로 보내면 게이트웨이가 EGW00116 으로 거절한다.
    is_form = str(api.get("content_type") or "").lower().startswith(
        "application/x-www-form-urlencoded")
    # 인증 계열은 토큰이 필요 없다. authorization 을 붙이면 토큰을 받으려고
    # 토큰을 먼저 발급받아야 하는 순환이 된다.
    needs_token = api["category"] != "oauth2"
    is_oauth = not needs_token
    degraded = bool(catalog and any(
        f.get("degraded") or f["kind"].startswith("응답")
        for f in catalog.corrections_for(api.key)))
    # 경고 확인 흐름이 있는 API — 요청에 warn_cnfr_yn 이 있으면 응답에 경고가 온다
    warns = any(p["name"] == "warn_cnfr_yn" for p in api.params)

    head = [f'"""메리츠 Open API — {clean_text(api.name)}', "",
            f"  {api.method} {api.path}",
            f"  TR {api['tr_id']}" + (f"   TPS {api['tps']}" if api.get("tps") else "")]
    if is_form:
        head += ["",
                 "  본문은 form-urlencoded 로 보냅니다. JSON 으로 보내면 EGW00116 으로",
                 "  거절됩니다(content-type 을 함께 맞춰야 합니다)."]
    if is_oauth:
        head += ["",
                 "  인증 계열이라 authorization 헤더를 붙이지 않습니다 —",
                 "  본문의 앱키·시크릿이 곧 인증입니다. 헤더에 토큰을 붙이면",
                 "  토큰을 받으려고 토큰을 먼저 발급받아야 하는 순환이 됩니다."]
    head += _warnings(api, catalog)
    head += ["", "준비", "  pip install requests",
             "  export MERITZ_APP_KEY=발급받은_앱키",
             "  export MERITZ_APP_SECRET=발급받은_시크릿", "",
             "요청은 운영 서버로 나갑니다.", '"""']

    sig = [f'{safe_name(p["name"])}: {_hint(p)}' for p in api.required]
    sig += [f'{safe_name(p["name"])}: {_hint(p)} | None = None' for p in api.optional]
    if is_post:
        sig.append("*, confirm: bool = False")

    body = ["", "", f'def {fn}({", ".join(sig)}) -> dict:', f'    """{clean_text(api.name)}']
    if is_post:
        body += ["", "    실제로 전송되는 요청입니다. confirm=True 를 넘겨야 나갑니다."]
    body += _param_doc(api)
    body.append('    """')

    holder = "payload" if is_post else "params"
    if api.required:
        body.append(f"    {holder} = {{")
        body += [f'        "{p["name"]}": {safe_name(p["name"])},' for p in api.required]
        body.append("    }")
    else:
        body.append(f"    {holder}: dict[str, Any] = {{}}")
    if api.optional:
        body.append("    for _k, _v in {")
        body += [f'        "{p["name"]}": {safe_name(p["name"])},' for p in api.optional]
        body += ["    }.items():", "        if _v is not None:",
                 f"            {holder}[_k] = _v"]

    if is_post:
        # 인증 요청의 본문에는 시크릿과 토큰이 들어 있다. 확인 단계에서
        # 그대로 찍으면 자격증명이 화면·로그에 남는다.
        shown = ("payload" if not is_oauth else
                 '{_k: ("***" if _k in _MASK else _v)\n'
                 '                              for _k, _v in payload.items()}')
        body += ["", "    if not confirm:",
                 "        # 확인 전에는 보내지 않는다. 내용을 확인하고 confirm=True 로 다시 부른다.",
                 f'        return {{"needs_confirmation": True, "will_send": {shown},',
                 f'                "endpoint": "{api.method} {api.path}"}}']

    body += ["", "    headers = {"]
    if needs_token:
        body += ['        "authorization": f"Bearer {get_token()}",',
                 '        "mac_address": _mac_address(),']
    if is_post:
        body.append('        "content-type": "%s",' % (
            "application/x-www-form-urlencoded" if is_form
            else "application/json; charset=utf-8"))
    body.append("    }")

    if is_post:
        sent = "data=payload" if is_form else "json=payload"
        body += [f'    resp = requests.post(f"{{BASE_URL}}{api.path}", {sent},',
                 "                         headers=headers, timeout=TIMEOUT)"]
    else:
        body += [f'    resp = requests.get(f"{{BASE_URL}}{api.path}", params=params,',
                 "                        headers=headers, timeout=TIMEOUT)"]
    body += ["", "    try:", "        out = resp.json()", "    except ValueError:",
             "        out = resp.text", "    return check(resp.status_code, out)"]

    ev = example_values(api, catalog)

    def _ex(p) -> str:
        v = ev.get(p["name"], 0 if p.get("type") == "number" else "")
        expr = _PLACEHOLDERS.get(v.strip()) if isinstance(v, str) else None
        return f'{safe_name(p["name"])}={expr or repr(v)}'

    call = [_ex(p) for p in api.required]
    if is_post:
        call.append("confirm=False")
    # 진입점에서 MeritzError 를 잡는다. 안 잡으면 앱키가 틀렸을 때
    # 잘 쓴 오류 메시지가 트레이스백에 묻힌다.
    tail = ["", "", 'if __name__ == "__main__":', "    try:",
            f'        result = {fn}({", ".join(call)})',
            "    except MeritzError as e:",
            '        raise SystemExit(f"{e}") from None',
            "    print(result)"]
    if is_post:
        tail.append("    # 내용을 확인했다면 confirm=True 로 다시 호출합니다.")
    if warns:
        first = [c for c in call if not c.startswith("confirm")]
        tail += ["",
                 "    # 경고가 붙으면 접수되지 않습니다. 내용을 사용자에게 보이고",
                 '    # 동의를 받은 뒤 warn_cnfr_yn="A" 로 다시 보내야 접수됩니다.',
                 "    # try:",
                 f'    #     {fn}({", ".join(first)}, confirm=True)',
                 "    # except MeritzWarning as w:",
                 '    #     print("경고:", w)',
                 f'    #     {fn}({", ".join(c for c in first if "warn_cnfr_yn" not in c)},',
                 '    #          warn_cnfr_yn="A", confirm=True)']
    if any(p["name"] == "tr_cont" for p in api.params):
        tail += ["", '    # 연속 조회 — rsp_cd 가 "5762" 면 다음 페이지가 있습니다.',
                 '    # while result.get("rsp_cd") == "5762":',
                 f'    #     result = {fn}({_args_prefix(call)}tr_cont="1",',
                 '    #                    tr_cont_key=result.get("tr_cont_key", ""))']

    # 조회 API 는 요청한 종목이 응답에 돌아오는지 확인한다.
    echo = (api.method == "GET"
            and any(p["name"] in ("iscd", "shrn_iscd") for p in api.params))

    parts = ["\n".join(head), _COMMON]
    if warns:
        scheme = "overseas" if "/overseas/" in api["path"] else "domestic"
        parts.append(_WARN_CLASS % (RESEND_OK[scheme],))
    if degraded or echo:
        parts.append(_EMPTY_FN)
    parts += ["\n".join(body),
              _OAUTH_CHECK if is_oauth else _check_fn(degraded, warns, echo),
              "\n".join(tail)]
    return "\n".join(parts)


def build_websocket(api, catalog=None) -> str:
    sub = api.get("subscribe") or {}
    tr_cd = sub.get("tr_cd")
    key_field = sub.get("tr_key")
    need_key = bool(key_field)
    fn = api.key
    arg = "tr_key: str, " if need_key else ""

    head = [f'"""메리츠 Open API 실시간 — {clean_text(api.name)}', "",
            f"  구독 코드 {tr_cd}",
            f"  접속      {PROD_WS}", "",
            "  접속점은 하나입니다. 무엇을 받을지는 구독 메시지의 tr_cd 가 정합니다.",
            "  API 마다 경로가 나뉘지 않습니다.", "",
            "준비", "  pip install websockets requests",
            "  export MERITZ_APP_KEY=발급받은_앱키",
            "  export MERITZ_APP_SECRET=발급받은_시크릿", "",
            "토큰 발급과 구독 접속 모두 운영 서버로 나갑니다.", '"""']

    pre = '''from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Callable

import requests
import websockets

BASE_URL = os.getenv("MERITZ_BASE_URL", "%s").rstrip("/")
WS_URL = os.getenv("MERITZ_WS_URL", "%s")
APP_KEY = os.getenv("MERITZ_APP_KEY")
APP_SECRET = os.getenv("MERITZ_APP_SECRET")

TR_CD = "%s"
_token: dict[str, Any] = {"value": None, "expires_at": 0.0}


class MeritzError(RuntimeError):
    pass


def get_token() -> str:
    """접근토큰. 웹소켓은 접속이 아니라 구독 메시지에서 인증합니다."""
    if _token["value"] and time.time() < _token["expires_at"]:
        return _token["value"]
    if not APP_KEY or not APP_SECRET:
        raise MeritzError("MERITZ_APP_KEY / MERITZ_APP_SECRET 환경변수가 필요합니다.")
    resp = requests.post(
        f"{BASE_URL}/oauth2/token",
        data={"grant_type": "client_credentials", "client_id": APP_KEY,
              "client_secret": APP_SECRET, "scope": "login"},
        headers={"content-type": "application/x-www-form-urlencoded"}, timeout=15)
    if resp.status_code != 200:
        # 앱키가 틀리면 EGW00103 이 온다. 어느 서버로 보냈는지 함께 보여준다.
        raise MeritzError(f"토큰 발급 실패 (HTTP {resp.status_code}): {resp.text} "
                          f"— 요청한 서버는 {BASE_URL} 입니다.")
    data = resp.json()
    _token["value"] = data["access_token"]
    _token["expires_at"] = time.time() + int(data.get("expires_in", 43200)) - 60
    return _token["value"]
''' % (PROD, PROD_WS, tr_cd)

    b = ["", "", f'def subscribe_message({arg}tr_type: str = "1") -> str:',
         '    """구독 메시지. tr_type 은 "1" 등록 / "2" 해지."""',
         '    body: dict[str, str] = {"tr_cd": TR_CD}']
    if need_key:
        b.append('    body["tr_key"] = tr_key')
    b += ["    return json.dumps({",
          '        "header": {"token": f"Bearer {get_token()}", "tr_type": tr_type},',
          '        "body": body,', "    })", "", "",
          f'async def {fn}({arg}on_data: Callable[[dict], None] = print) -> None:']
    doc = [f'    """{clean_text(api.name)} 를 구독해 받는 대로 on_data 로 넘깁니다.', ""]
    if need_key:
        doc.append(f'    tr_key  {clean_text(key_field.get("name_ko"))}')
        if "@" in api.example_request:
            doc.append('            해외는 <거래소>@<종목> 형식입니다. 예) "OQ@NVDA"')
        doc += ["",
                "    주의 — 서버는 tr_key 의 종목코드를 검사하지 않습니다.",
                '    없는 종목을 넣어도 구독은 "00000" 으로 성공하고 데이터만 오지 않습니다.']
    else:
        doc += ["    구독 대상은 접근토큰에 묶인 사용자로 정해집니다. tr_key 를 넣지 않습니다.",
                "",
                "    주문이 있어야 데이터가 옵니다. 구독만으로는 아무것도 오지 않습니다."]
    doc.append('    """')
    b.append("\n".join(doc))
    b += ['    async with websockets.connect(WS_URL, ping_interval=20) as ws:',
          f'        await ws.send(subscribe_message({"tr_key" if need_key else ""}))',
          "        async for raw in ws:",
          "            msg = json.loads(raw)",
          '            header = msg.get("header") or {}',
          "",
          "            # 오류는 봉투 없이 최상위로 옵니다.",
          '            if "rsp_cd" in msg and not header:',
          '                raise MeritzError(f\'{msg["rsp_cd"]} — {msg.get("rsp_msg")}\')',
          "",
          "            # 구독 응답에는 header.rsp_cd 가 있고, 데이터에는 없습니다.",
          '            if "rsp_cd" in header:',
          '                if header["rsp_cd"] != "00000":',
          "                    raise MeritzError(",
          '                        f\'구독 실패 {header["rsp_cd"]} — {header.get("rsp_msg")}\')',
          "                print(f'구독 완료 — {TR_CD}')",
          "                continue",
          "",
          '            payload = msg.get("body")',
          '            if payload is not None:      # keepalive 등 빈 프레임은 넘긴다',
          '                on_data(payload)']

    key_ex = ""
    if need_key:
        m = re.search(r'"tr_key"\s*:\s*"([^"]+)"', api.example_request)
        key_ex = f'"{m.group(1) if m else "005930"}"'
    tail = ["", "", 'if __name__ == "__main__":', "    try:",
            f"        asyncio.run({fn}({key_ex}))",
            "    except MeritzError as e:",
            '        raise SystemExit(f"{e}") from None']
    return "\n".join(["\n".join(head), pre, "\n".join(b), "\n".join(tail)])


def build_token() -> str:
    return ('"""메리츠 Open API — 접근토큰 발급\n\n'
            "  POST /oauth2/token\n\n"
            "  form-urlencoded 로 보내야 합니다. JSON 으로 보내면 EGW00116 으로 거절됩니다.\n"
            "  토큰은 12시간 유효하며, 이 코드는 만료 60초 전까지 재사용합니다.\n"
            '"""\n' + _COMMON +
            '\n\nif __name__ == "__main__":\n    try:\n        print(get_token()[:20] + "...")\n'
            '    except MeritzError as e:\n        raise SystemExit(f"{e}") from None\n')
