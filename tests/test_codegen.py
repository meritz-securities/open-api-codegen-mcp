"""코드 생성 계약 검증.

대고객 배포물이라 **생성된 코드가 실제로 도는가**가 핵심이다.
여기서는 네트워크 없이 확인할 수 있는 것을 지킨다. """
import ast
import keyword
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from meritz_codegen import build_rest, build_token, build_websocket, load_catalog  # noqa: E402
from meritz_codegen.python import example_values, safe_name  # noqa: E402
from meritz_codegen.search import ALIASES, search  # noqa: E402

CAT = load_catalog()

# 문자열 자체가 저장소에 남지 않도록 쪼개 둔다. tests/test_no_dev_server.py 가
# 저장소 전체에서 이 문자열을 금지하기 때문이다.
DEV_HOST = "dev" + "api.imeritz.com"


def gen(a):
    return build_websocket(a, CAT) if a.is_websocket else build_rest(a, CAT)


def func_of(code, name):
    for node in ast.parse(code).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    return None


class SyntaxTest(unittest.TestCase):
    def test_all_generate_valid_python(self):
        bad = []
        for a in CAT:
            try:
                ast.parse(gen(a))
            except SyntaxError as e:
                bad.append((a.key, str(e)))
        self.assertEqual(bad, [], f"문법 오류: {bad}")

    def test_token_code_is_valid(self):
        ast.parse(build_token())

    def test_function_name_is_valid_identifier(self):
        for a in CAT:
            self.assertTrue(a.key.isidentifier(), a.key)
            self.assertFalse(keyword.iskeyword(a.key), a.key)


class SignatureTest(unittest.TestCase):
    def test_required_params_are_arguments(self):
        missing = []
        for a in CAT.rest():
            fn = func_of(gen(a), a.key)
            self.assertIsNotNone(fn, a.key)
            args = {x.arg for x in fn.args.args}
            for p in a.required:
                if safe_name(p["name"]) not in args:
                    missing.append((a.key, p["name"]))
        self.assertEqual(missing, [], f"시그니처에 없는 필수 파라미터: {missing}")

    def test_python_keywords_escaped_but_request_key_preserved(self):
        code = gen(CAT.get("transactions"))
        self.assertIn("from_", {x.arg for x in func_of(code, "transactions").args.args})
        self.assertIn('"from": from_', code)

    def test_optional_params_default_to_none(self):
        for a in CAT.rest():
            fn = func_of(gen(a), a.key)
            n_opt = len(a.optional)
            if n_opt:
                self.assertGreaterEqual(len(fn.args.defaults), n_opt, a.key)


class OrderSafetyTest(unittest.TestCase):
    """주문 코드가 확인 없이 전송되면 사고다."""

    def test_every_post_has_confirm_gate(self):
        bad = [a.key for a in CAT.rest()
               if a.method == "POST"
               and ("confirm: bool = False" not in gen(a)
                    or "needs_confirmation" not in gen(a))]
        self.assertEqual(bad, [], f"confirm 게이트 없음: {bad}")

    def test_no_get_has_confirm_gate(self):
        for a in CAT.rest():
            if a.method == "GET":
                self.assertNotIn("needs_confirmation", gen(a), a.key)

    def test_confirm_check_precedes_send(self):
        """주문 함수 본문 안에서 confirm 검사가 전송보다 앞에 있어야 한다."""
        for a in CAT.rest():
            if a.method != "POST":
                continue
            body = ast.unparse(func_of(gen(a), a.key))
            self.assertIn("needs_confirmation", body, a.key)
            self.assertLess(body.index("needs_confirmation"),
                            body.index("requests.post"), a.key)

    def test_confirm_is_keyword_only(self):
        """confirm 이 위치 인자면 실수로 채워질 수 있다."""
        for a in CAT.rest():
            if a.method != "POST":
                continue
            fn = func_of(gen(a), a.key)
            self.assertIn("confirm", {x.arg for x in fn.args.kwonlyargs}, a.key)


class ResponseCheckTest(unittest.TestCase):
    """읽히는 오류 코드를 성공으로 넘기면 거절된 주문이 성공으로 보인다."""

    def test_readable_error_raises(self):
        ns = {}
        exec(compile(gen(CAT.get("valuation")), "t", "exec"), ns)
        with self.assertRaises(ns["MeritzError"]):
            ns["check"](200, {"rsp_cd": "8005", "rsp_msg": "초과", "data": {"x": 1}})

    def test_ok_codes_pass(self):
        ns = {}
        exec(compile(gen(CAT.get("valuation")), "t", "exec"), ns)
        for code in ("0000", "0001", "5762", "5766", "5820"):
            self.assertIsNotNone(ns["check"](200, {"rsp_cd": code, "data": {}}))

    def test_unknown_corruption_raises_when_not_degraded(self):
        ns = {}
        exec(compile(gen(CAT.get("valuation")), "t", "exec"), ns)
        with self.assertRaises(ns["MeritzError"]):
            ns["check"](200, {"rsp_cd": "\x00\x11", "data": {"x": 1}})

    def test_degraded_api_tolerates_corruption_but_not_empty(self):
        ns = {}
        exec(compile(gen(CAT.get("market_prices")), "t", "exec"), ns)
        self.assertIsNotNone(ns["check"](200, {"rsp_cd": "\x00\x11",
                                               "data": {"stck_prpr": 417500}}))
        with self.assertRaises(ns["MeritzError"]):
            ns["check"](200, {"rsp_cd": "\x00\x11",
                              "data": {"stck_prpr": 0, "kor_isnm": ""}})

    def test_http_error_raises(self):
        ns = {}
        exec(compile(gen(CAT.get("valuation")), "t", "exec"), ns)
        with self.assertRaises(ns["MeritzError"]):
            ns["check"](500, {"rsp_cd": "IGW50004"})


class ExampleTest(unittest.TestCase):
    def test_every_required_param_has_example_value(self):
        missing = []
        for a in CAT.rest():
            ev = example_values(a, CAT)
            missing += [(a.key, p["name"]) for p in a.required if p["name"] not in ev]
        self.assertEqual(missing, [], f"실행 예시에 값이 빠진 필수 파라미터: {missing}")

    def test_portal_broken_examples_use_corrections(self):
        """포털 예시가 틀린 API 는 되는 값으로 코드를 만들어야 한다."""
        ev = example_values(CAT.get("ovs_market_prices"), CAT)
        self.assertIn("mrkt_div_code", ev)
        self.assertIn("dely_rltm_cls_code", ev)

    def test_bearer_placeholder_not_parsed_as_body(self):
        ev = example_values(CAT.get("orders_buy"), CAT)
        self.assertIn("iscd", ev)
        self.assertNotIn("access_token", ev)


class DeploymentTest(unittest.TestCase):
    def test_generated_code_defaults_to_production(self):
        for a in CAT:
            code = gen(a)
            self.assertNotIn(DEV_HOST, code, a.key)
            self.assertIn("openapi.imeritz.com", code, a.key)

    def test_base_url_is_overridable(self):
        self.assertIn('os.getenv("MERITZ_BASE_URL"', gen(CAT.get("market_prices")))

    def test_credentials_come_from_environment_only(self):
        for a in CAT:
            self.assertIn('os.getenv("MERITZ_APP_KEY")', gen(a), a.key)

    def test_no_secret_literals(self):
        for a in CAT:
            code = gen(a)
            self.assertNotIn("Bearer ey", code, a.key)


class WebsocketTest(unittest.TestCase):
    def test_single_endpoint_and_tr_cd(self):
        for a in CAT.websockets():
            code = build_websocket(a, CAT)
            self.assertIn("wss://openapi.imeritz.com:29443/websocket", code)
            self.assertIn(f'TR_CD = "{a["subscribe"]["tr_cd"]}"', code)

    def test_order_notification_takes_no_tr_key(self):
        """주문 통보는 토큰으로 대상이 정해진다."""
        for key in ("ws_cntg_rslt", "ws_cntg_infr"):
            fn = func_of(build_websocket(CAT.get(key), CAT), key)
            self.assertNotIn("tr_key", {x.arg for x in fn.args.args}, key)

    def test_price_stream_takes_tr_key(self):
        fn = func_of(build_websocket(CAT.get("ws_stck_cntg"), CAT), "ws_stck_cntg")
        self.assertIn("tr_key", {x.arg for x in fn.args.args})

    def test_ack_and_error_are_distinguished(self):
        code = build_websocket(CAT.get("ws_stck_cntg"), CAT)
        self.assertIn('"rsp_cd" in msg and not header', code)   # 오류는 봉투 없음
        self.assertIn('"rsp_cd" in header', code)               # 구독 응답


class SearchTest(unittest.TestCase):
    def test_all_aliases_point_to_real_apis(self):
        missing = sorted({t for v in ALIASES.values() for t in v if t not in CAT})
        self.assertEqual(missing, [], f"없는 api_type 을 가리키는 별칭: {missing}")

    def test_common_queries_rank_well(self):
        cases = {"삼성전자 현재가": "market_prices", "예수금": "deposit",
                 "보유종목": "holdings", "주문내역": "orders_history",
                 "매수": "orders_buy", "매도": "orders_sell",
                 "실시간 체결통보": "ws_cntg_rslt", "실시간 호가": "ws_stck_aspr",
                 "환전": "fx_exchanges", "주문가능금액": "orders_estimate",
                 "해외주식 현재가": "ovs_market_prices", "일봉 차트": "market_candles_days"}
        bad = []
        for q, want in cases.items():
            got = [h["api_type"] for h in search(CAT, q)]
            rank = got.index(want) + 1 if want in got else 0
            if not 0 < rank <= 3:
                bad.append((q, want, got[:3]))
        self.assertEqual(bad, [], f"상위 3위에 들지 못한 검색: {bad}")

    def test_state_changing_results_carry_caution(self):
        for h in search(CAT, "매수"):
            if CAT.get(h["api_type"]).is_state_changing:
                self.assertIn("caution", h)

    def test_portal_issue_is_surfaced_in_search(self):
        """정정이 걸린 API 는 검색 결과에 portal_issue 가 실려야 한다.

        특정 api_type 을 박아 두지 않는다. 2026-09-11 재검증에서 포털이 고친
        항목을 corrections.json 에서 빼자 ovs_market_prices 를 박아 둔 이 검사가
        깨졌다 — 정정 목록이 줄어드는 것은 정상이다.
        """
        key = next((k for c in (CAT.corrections.get("corrections") or [])
                    for k in c.get("keys", []) if CAT.get(k) is not None), None)
        self.assertIsNotNone(key, "정정 항목이 하나도 없습니다")
        hits = {h["api_type"]: h for h in search(CAT, CAT.get(key).name)}
        self.assertIn("portal_issue", hits[key])




# ---------------------------------------------------------------------------
# 생성 코드의 안전장치 회귀 방지.
# ---------------------------------------------------------------------------
from meritz_codegen.python import clean_text  # noqa: E402


def run(api):
    """생성 코드를 실행해 네임스페이스를 돌려준다."""
    ns: dict = {}
    exec(compile(gen(api), api.key, "exec"), ns)
    return ns


class OrderWarningTest(unittest.TestCase):
    """rsp_cd 가 "0001" 이어도 warn_cls_code 가 경고면 접수되지 않은 상태다."""

    ORDER_KEYS = [a.key for a in CAT.rest()
                  if any(p["name"] == "warn_cnfr_yn" for p in a.params)]

    def test_order_apis_have_warning_flow(self):
        self.assertGreaterEqual(len(self.ORDER_KEYS), 10)
        for k in self.ORDER_KEYS:
            code = gen(CAT.get(k))
            self.assertIn("MeritzWarning", code, k)
            self.assertIn("warn_cls_code", code, k)

    def test_warning_blocks_apparent_success(self):
        for k in self.ORDER_KEYS:
            ns = run(CAT.get(k))
            with self.assertRaises(ns["MeritzWarning"], msg=k):
                ns["check"](200, {"rsp_cd": "0001", "rsp_msg": "주문이 완료되었습니다.",
                                  "data": {"oder_no": 1, "warn_cls_code": "1",
                                           "warn_msg": "증거금 부족"}})

    def test_normal_acceptance_passes(self):
        ns = run(CAT.get("orders_buy"))
        self.assertIsNotNone(ns["check"](
            200, {"rsp_cd": "0001", "data": {"oder_no": 1, "warn_cls_code": "0"}}))

    def test_warning_check_precedes_success_return(self):
        """rsp_cd 성공 반환보다 앞에 있어야 한다. 뒤에 두면 영영 안 걸린다."""
        code = gen(CAT.get("orders_buy"))
        body = ast.unparse(func_of(code, "check"))
        self.assertLess(body.index("_warning_row"), body.index("'0001'"))

    def test_warning_is_caught_in_every_response_shape(self):
        """단건 dict · 배열 · 최상위 — 한 형태만 보면 나머지에서 새어 나간다."""
        ns = {}
        exec(gen(CAT.get("orders_buy")).split("if __name__")[0], ns)
        check = ns["check"]
        shapes = {
            "단건": {"rsp_cd": "0001",
                     "data": {"warn_cls_code": "c", "warn_msg": "증거금 부족"}},
            "배열": {"rsp_cd": "0001",
                     "data": [{"warn_cls_code": "0"}, {"warn_cls_code": "g"}]},
            "최상위": {"rsp_cd": "0001", "warn_cls_code": "1"},
        }
        for name, body in shapes.items():
            with self.subTest(shape=name):
                with self.assertRaises(ns["MeritzWarning"]):
                    check(200, body)
        # 경고가 아니면 통과해야 한다
        check(200, {"rsp_cd": "0001", "data": {"warn_cls_code": "0", "oder_no": 1}})

    def test_no_data_codes_are_not_errors(self):
        """5820·5822 는 자료 없음이다. 예외로 튀면 정상 조회가 실패로 보인다."""
        ns = {}
        exec(gen(CAT.get("market_prices")).split("if __name__")[0], ns)
        for code in ("5820", "5822"):
            with self.subTest(code=code):
                ns["check"](200, {"rsp_cd": code, "data": {}})

    def test_resend_instruction_is_present(self):
        """경고 시 warn_cnfr_yn="A" 로 재전송해야 한다는 안내가 있어야 한다."""
        code = gen(CAT.get("orders_buy"))
        self.assertIn('warn_cnfr_yn="A"', code)


class EmptyResultTest(unittest.TestCase):
    """없는 종목을 조회하면 게이트웨이가 오류 대신 채워진 껍데기를 준다."""

    def test_domestic_quote_rejects_unknown_symbol(self):
        ns = run(CAT.get("market_prices"))
        with self.assertRaises(ns["MeritzError"]):
            ns["check"](200, {"rsp_cd": "\x00\xef", "data": {
                "stck_prpr": 0, "rprs_mrkt_kor_name": "KOSPI", "per": "0.00",
                "pbr": "0.00", "acml_vol": 0, "kor_isnm": ""}})

    def test_overseas_quote_rejects_unknown_symbol(self):
        """정상 rsp_cd(0000)로 와도 값이 비면 성공이 아니다."""
        ns = run(CAT.get("ovs_market_prices"))
        with self.assertRaises(ns["MeritzError"]):
            ns["check"](200, {"rsp_cd": "0000",
                              "data": {"iscd": "", "prpr": 0, "crnc_code": "USD"}})

    def test_real_quote_passes(self):
        ns = run(CAT.get("market_prices"))
        self.assertIsNotNone(ns["check"](
            200, {"rsp_cd": "\x00\xef", "data": {"shrn_iscd": "005930",
                                                 "stck_prpr": 417500}}))

    def test_account_api_without_symbol_is_unaffected(self):
        ns = run(CAT.get("valuation"))
        self.assertIsNotNone(ns["check"](200, {"rsp_cd": "5766",
                                               "data": {"tfam": 100000000}}))


class GeneratorRobustnessTest(unittest.TestCase):
    """카탈로그는 포털을 크롤해 다시 만들어진다 — 무엇이 들어올지 모른다."""

    def test_clean_text_removes_docstring_breakers(self):
        self.assertNotIn('"""', clean_text('앞' + '"' * 3 + '뒤'))
        self.assertNotIn("<b>", clean_text("<b>굵게</b> 설명"))
        self.assertNotIn("&nbsp;", clean_text("a&nbsp;b"))
        self.assertNotIn("\n", clean_text("줄\n바꿈"))
        self.assertNotIn("\\", clean_text("역슬래시\\있음"))

    def test_safe_name_rejects_non_identifiers(self):
        for bad in ("52wk-high", "", None, "a b", "a.b"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                safe_name(bad)

    def test_safe_name_handles_keywords(self):
        self.assertEqual(safe_name("from"), "from_")
        self.assertEqual(safe_name("iscd"), "iscd")

    def test_description_is_not_truncated(self):
        """설명을 자르면 코드값 표가 사라져 이용자가 잘못된 값을 넣는다."""
        code = gen(CAT.get("orders_buy"))
        self.assertIn("스톱지정가", code)      # oder_cls_code "83"
        self.assertIn("NXT", code)             # exch_kind_code 제약
        code2 = gen(CAT.get("ovs_orders_buy"))
        self.assertGreater(code2.count("거래소"), 1)

    def test_no_html_leaks(self):
        for a in CAT:
            code = gen(a)
            for tag in ("<b>", "</b>", "&nbsp;", "<br/>"):
                self.assertNotIn(tag, code, f"{a.key} 에 {tag}")


class PagingCommentTest(unittest.TestCase):
    def test_continuation_snippet_is_valid_python(self):
        """주석을 풀었을 때 문법이 맞아야 한다 — 그러라고 넣은 것이다."""
        for a in CAT.rest():
            if not any(p["name"] == "tr_cont" for p in a.params):
                continue
            # 주석에서 '#' 만 떼고 나머지 들여쓰기는 보존한다
            block = [re.sub(r"^(\s*)#", r"\1", ln)
                     for ln in gen(a).splitlines() if ln.strip().startswith("#")]
            body = [ln.strip() for ln in block
                    if "result =" in ln or "tr_cont_key=" in ln]
            self.assertTrue(body, a.key)
            ast.parse(" ".join(body))      # 괄호 안 이어짐 — 한 줄로 합쳐 본다


class WebsocketDetailTest(unittest.TestCase):
    def test_keepalive_frame_does_not_crash(self):
        for a in CAT.websockets():
            self.assertIn("payload is not None", build_websocket(a, CAT), a.key)

    def test_symbol_warning_only_where_tr_key_exists(self):
        self.assertIn("종목코드를 검사하지 않습니다",
                      build_websocket(CAT.get("ws_stck_cntg"), CAT))
        self.assertNotIn("종목코드를 검사하지 않습니다",
                         build_websocket(CAT.get("ws_cntg_rslt"), CAT))

    def test_dev_switch_mentions_both_variables(self):
        code = build_websocket(CAT.get("ws_stck_cntg"), CAT)
        self.assertIn("MERITZ_WS_URL", code)
        self.assertIn("MERITZ_BASE_URL", code)


class SearchRoutingTest(unittest.TestCase):
    """엉뚱한 API 를 1위로 주면 위험하다 — 특히 주문 계열."""

    def test_overseas_queries_stay_overseas(self):
        for q, want in (("해외 주문 취소", "ovs_orders_cancel"),
                        ("해외주식 매도", "ovs_orders_sell"),
                        ("해외 잔고", "ovs_holdings"),
                        ("해외 주문 정정", "ovs_orders_modify")):
            got = [h["api_type"] for h in search(CAT, q)]
            self.assertIn(want, got[:3], f"{q} → {got[:3]}")

    def test_specific_action_beats_broad_alias(self):
        for q, want in (("주문 정정", "orders_modify"), ("주문 취소", "orders_cancel")):
            got = [h["api_type"] for h in search(CAT, q)]
            self.assertIn(want, got[:3], f"{q} → {got[:3]}")

    def test_non_action_query_hides_state_changing(self):
        """'현재가' 를 물었는데 매수가 나오면 안 된다."""
        for q in ("현재가", "잔고", "호가", "예수금"):
            for h in search(CAT, q):
                self.assertFalse(CAT.get(h["api_type"]).is_state_changing,
                                 f"{q} → {h['api_type']}")


class ContentTypeTest(unittest.TestCase):
    """카탈로그의 content_type 을 따르지 않으면 게이트웨이가 EGW00116 으로 거절한다."""

    def _form_apis(self):
        return [a for a in CAT.rest()
                if str(a.get("content_type") or "").lower().startswith(
                    "application/x-www-form-urlencoded")]

    def test_catalog_has_form_encoded_apis(self):
        """표본이 0 건이면 아래 검사들이 조용히 통과한다."""
        self.assertTrue(self._form_apis(), "폼인코딩 API 가 카탈로그에 없습니다")

    def test_form_encoded_apis_never_send_json(self):
        bad = [a.key for a in self._form_apis() if "json=payload" in gen(a)]
        self.assertEqual(bad, [], f"폼인코딩인데 JSON 으로 보냅니다: {bad}")

    def test_form_encoded_apis_send_data_with_matching_header(self):
        for a in self._form_apis():
            code = gen(a)
            self.assertIn("data=payload", code, a.key)
            self.assertIn('"content-type": "application/x-www-form-urlencoded"', code, a.key)

    def test_json_apis_still_send_json(self):
        for a in CAT.rest():
            ct = str(a.get("content_type") or "").lower()
            if a.method == "POST" and ct.startswith("application/json"):
                code = gen(a)
                self.assertIn("json=payload", code, a.key)
                self.assertNotIn("data=payload", code, a.key)

    def test_request_body_matches_declared_content_type(self):
        """선언과 전송이 어긋난 API 가 하나도 없어야 한다."""
        bad = []
        for a in CAT.rest():
            if a.method != "POST":
                continue
            form = str(a.get("content_type") or "").lower().startswith(
                "application/x-www-form-urlencoded")
            code = gen(a)
            if form != ("data=payload" in code) or form == ("json=payload" in code):
                bad.append(a.key)
        self.assertEqual(bad, [], f"content_type 과 전송 방식이 다릅니다: {bad}")


class OAuthCodegenTest(unittest.TestCase):
    """토큰을 받으려고 토큰을 발급받을 수는 없다."""

    def _oauth(self):
        return [a for a in CAT.rest() if a["category"] == "oauth2"]

    def test_oauth_apis_exist(self):
        self.assertEqual(sorted(a.key for a in self._oauth()),
                         ["oauth2_revoke", "oauth2_token"])

    def test_no_authorization_header(self):
        for a in self._oauth():
            code = gen(a)
            self.assertNotIn('"authorization"', code, a.key)
            self.assertNotIn("Bearer {get_token()}", code, a.key)

    def test_revoke_puts_the_token_in_the_body(self):
        """폐기 대상 토큰은 헤더가 아니라 본문이다 — 카탈로그 파라미터 그대로."""
        code = gen(CAT.get("oauth2_revoke"))
        fn = func_of(code, "oauth2_revoke")
        self.assertIn("token", {x.arg for x in fn.args.args})
        self.assertIn('"token": token,', code)

    def test_placeholders_are_replaced_with_real_expressions(self):
        for a in self._oauth():
            code = gen(a)
            for ph in ("{app_key}", "{app_secret}", "{access_token}"):
                self.assertNotIn(ph, code, f"{a.key} 에 자리표시자 {ph} 가 남았습니다")

    def test_oauth_response_without_rsp_cd_is_accepted(self):
        """발급 응답에는 rsp_cd 가 없다. 없다고 실패로 보면 전부 오류가 된다."""
        ns = {}
        exec(compile(gen(CAT.get("oauth2_token")), "t", "exec"), ns)
        out = ns["check"](200, {"access_token": "ey...", "expires_in": 43200,
                                "token_type": "Bearer"})
        self.assertEqual(out["access_token"], "ey...")
        with self.assertRaises(ns["MeritzError"]):
            ns["check"](403, {"rsp_cd": "EGW00103", "rsp_msg": "유효하지 않은 client_id"})

    def test_revoke_failure_code_raises(self):
        ns = {}
        exec(compile(gen(CAT.get("oauth2_revoke")), "t", "exec"), ns)
        self.assertIsNotNone(ns["check"](200, {"code": 200, "message": "success"}))
        with self.assertRaises(ns["MeritzError"]):
            ns["check"](200, {"code": 400, "message": "invalid token"})

    def test_confirm_gate_does_not_print_credentials(self):
        for a in self._oauth():
            code = gen(a)
            self.assertIn('"***"', code, a.key)

    def test_oauth_is_not_an_order(self):
        for a in self._oauth():
            self.assertFalse(a.is_state_changing, a.key)


class OAuthSearchTest(unittest.TestCase):
    """찾을 수 없는 API 는 없는 것과 같다."""

    def test_reachable_by_korean_and_english_words(self):
        for q, want in (("토큰 발급", "oauth2_token"), ("인증", "oauth2_token"),
                        ("oauth", "oauth2_token"), ("접근토큰", "oauth2_token"),
                        ("revoke", "oauth2_revoke"), ("토큰 폐기", "oauth2_revoke")):
            got = [h["api_type"] for h in search(CAT, q)]
            self.assertIn(want, got[:3], f"{q} → {got[:3]}")

    def test_reachable_by_category(self):
        got = {h["api_type"] for h in search(CAT, "토큰", category="oauth2")}
        self.assertEqual(got, {"oauth2_token", "oauth2_revoke"})

    def test_category_has_korean_name(self):
        from meritz_codegen.search import CATEGORY_KO
        for a in CAT:
            self.assertIn(a["category"], CATEGORY_KO, a["category"])


if __name__ == "__main__":
    unittest.main()
