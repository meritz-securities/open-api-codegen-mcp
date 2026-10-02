# 메리츠증권 Open API 코드 생성 MCP

> 현재 베타 서비스 기간입니다.

[개발자 포털](https://openapi.imeritz.com) · [API 신청](https://openapi.imeritz.com/api-apply) · [API 문서](https://openapi.imeritz.com/apiservice) · [문의](https://openapi.imeritz.com/qna)

[![test](https://github.com/meritz-securities/open-api-codegen-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/meritz-securities/open-api-codegen-mcp/actions/workflows/test.yml) [![release](https://img.shields.io/github/v/release/meritz-securities/open-api-codegen-mcp?label=%EC%84%A4%EC%B9%98%20%ED%8C%8C%EC%9D%BC)](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest) [![python](https://img.shields.io/badge/python-3.11%2B-3776AB)](https://www.python.org/downloads/) [![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

메리츠증권 Open API를 호출하는 파이썬 코드를 만들어 주는 MCP 서버입니다.
API를 직접 호출하지 않으므로 앱키가 필요 없습니다. 내 PC에서 도는 로컬 서버이고,
단일 실행 파일이라 Python이나 uv를 따로 설치하지 않으셔도 됩니다.

REST 62건과 실시간 13건 전부를 다룹니다. 카탈로그는 개발자 포털 등록 명세에서 만듭니다.

## 설치

파일은 [릴리스 페이지](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest)에서 받으십시오.
쓰시는 것 하나만 받으시면 됩니다. 앱키를 넣는 자리는 없습니다.

| 쓰시는 도구 | 방법 |
|---|---|
| Claude Desktop | OS에 맞는 `.mcpb` 파일을 내려받아 더블클릭 — [Mac Apple 칩](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen-darwin-arm64.mcpb) · [Mac Intel](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen-darwin-x64.mcpb) · [Windows](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen-win32-x64.mcpb) |
| 아무 도구나 — 자동 설치 | `git clone` 후 `python3 install.py` — 실행 파일을 내려받고 등록 명령까지 만들어 줍니다 |
| Claude Code | `claude mcp add meritz-codegen -- <실행 파일 경로>` |
| Codex CLI · ChatGPT 데스크톱 | `codex mcp add meritz-codegen -- <실행 파일 경로>` |
| Gemini CLI | `gemini mcp add meritz-codegen <실행 파일 경로>` |
| Cursor · VS Code | 각 앱의 MCP 설정 파일에 JSON 을 넣습니다 — [`docs/install.md`](docs/install.md) |

실행 파일은 [meritz-codegen-mcp-darwin-arm64](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-codegen-mcp-darwin-arm64) ·
[meritz-codegen-mcp-darwin-x64](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-codegen-mcp-darwin-x64) ·
[meritz-codegen-mcp-win32-x64.exe](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-codegen-mcp-win32-x64.exe) 입니다.

Mac에서 직접 내려받으셨다면 실행 권한과 격리 속성 해제가 필요합니다.

```bash
chmod +x ~/Downloads/meritz-codegen-mcp-darwin-arm64
xattr -d com.apple.quarantine ~/Downloads/meritz-codegen-mcp-darwin-arm64
```

격리 속성이 남아 있으면 서버가 아무 메시지 없이 종료되어 도구 목록에 나타나지 않습니다.
OS 보안 경고, 체크섬 대조, 기동 대기 시간, Claude 웹·ChatGPT 웹용 터널 연결은
[`docs/install.md`](docs/install.md)에 있습니다.

## 써 보기

설치하고 클라이언트를 다시 시작하면 도구 다섯 개가 뜹니다. 그대로 물어보시면 됩니다.

```
삼성전자 현재가 조회하는 파이썬 코드 만들어 줘
해외 주문 취소는 어떤 API 써?
```

## 도구

| 도구 | 하는 일 |
|---|---|
| `list_categories()` | 분류와 API 개수 |
| `search_api(keyword, category)` | 자연어 검색. 한글 표현도 알아듣습니다 |
| `get_api_detail(api_type)` | 경로·파라미터·응답 필드·주의사항 |
| `generate_code(api_type)` | 호출 코드 (REST·실시간) |
| `api_conventions()` | 인증·호출 규약·응답 코드 |

`meritz_code_prompt(task, iscd)` 프롬프트도 함께 제공합니다. 검색부터 코드 생성까지의
순서를 안내합니다.

## 어떤 코드를 만드는지

- 토큰 발급·재사용, 요청, 응답 판정까지 들어갑니다. HTTP 200만 보고 넘기지 않습니다
- 연속 조회로 다음 페이지를 받는 방법을 주석으로 적어 줍니다
- 실시간은 웹소켓 구독 코드를 만듭니다. 접속점은 하나이고 `tr_cd`가 무엇을 받을지 정합니다
- 주문·환전 코드는 `confirm=True`를 넘기기 전까지 전송하지 않는 형태로 만듭니다
- 주문 코드에는 경고 확인 흐름이 들어갑니다. 응답이 성공이어도 `data.warn_cls_code`가
  `0`이 아니면 접수되지 않은 상태이므로, 생성된 코드가 `MeritzWarning`을 던집니다

응답 판정 규칙과 오류 코드 해석은 [`llms.txt`](llms.txt)에, 코드표는
[open-api 저장소의 docs/errors.md](https://github.com/meritz-securities/open-api/blob/main/docs/errors.md)에 있습니다.

## 저장소가 네 개입니다

| 하고 싶으신 일 | 여기로 |
|---|---|
| 호출 코드를 받아 쓰기 | **이 저장소** |
| 파이썬으로 직접 호출해 보기 | [open-api](https://github.com/meritz-securities/open-api) — 실행 예제 |
| 터미널에서 조회·주문하기 | [open-api-studio](https://github.com/meritz-securities/open-api-studio) — `meritz` CLI |
| AI 클라이언트에 붙이기 | [open-api-mcp](https://github.com/meritz-securities/open-api-mcp) — MCP 서버 |

## 개발

```bash
uv sync
uv run pytest tests/ -q

./build_binary.sh                    # bin/meritz-codegen-mcp — PyInstaller 단일 실행 파일
python3 make_bundle.py darwin-arm64  # dist/meritz-open-api-codegen-darwin-arm64.mcpb
```

릴리스는 태그를 밀면 GitHub Actions가 세 플랫폼을 빌드해 올립니다.

## 사용 전 확인해 주세요

- 생성된 코드는 운영 서버를 향합니다. 실행하시면 실계좌에 영향을 줍니다
- 주문 코드의 확인 단계를 지우시면 확인 없이 전송됩니다. 남겨 두시길 권합니다
- [DISCLAIMER.md](DISCLAIMER.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md)

## 라이선스

MIT — [LICENSE](LICENSE)

실행 파일에 함께 들어가는 오픈소스의 라이선스 전문은
[THIRD-PARTY-NOTICES.txt](THIRD-PARTY-NOTICES.txt) 에 있습니다.

문의는 개발자 포털을 이용해 주세요.
