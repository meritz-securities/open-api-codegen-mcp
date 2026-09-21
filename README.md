# 메리츠증권 Open API 코드 생성 MCP

[개발자 포털](https://openapi.imeritz.com) · [API 신청](https://openapi.imeritz.com/api-apply) · [API 문서](https://openapi.imeritz.com/apiservice) · [문의](https://openapi.imeritz.com/qna)

[![test](https://github.com/meritz-securities/open-api-codegen-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/meritz-securities/open-api-codegen-mcp/actions/workflows/test.yml) [![release](https://img.shields.io/github/v/release/meritz-securities/open-api-codegen-mcp?label=%EC%84%A4%EC%B9%98%20%ED%8C%8C%EC%9D%BC)](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest) [![python](https://img.shields.io/badge/python-3.11%2B-3776AB)](https://www.python.org/downloads/) [![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

메리츠증권 Open API를 호출하는 **파이썬 코드를 만들어 드리는** MCP 서버입니다.
API를 직접 호출하지 않으니 앱키도 필요 없습니다.

## 먼저 설치하세요

최신 고객용 설치파일은 [릴리스 페이지](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest)에서 받으십시오.

| 사용 환경 | 설치파일 |
|---|---|
| Claude Desktop — Mac Apple Silicon | [MCPB 다운로드](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen-darwin-arm64.mcpb) |
| Claude Desktop — Mac Intel | [MCPB 다운로드](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen-darwin-x64.mcpb) |
| Claude Desktop — Windows | [MCPB 다운로드](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen-win32-x64.mcpb) |
| Claude Code·Codex·Gemini·Cursor·VS Code | [OS별 실행파일](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest) |

앱키는 필요 없습니다. API를 실제로 호출하는 코드는 생성 후 별도로 실행합니다.

## 저장소가 네 개입니다

| 하고 싶으신 일 | 여기로 |
|---|---|
| 호출 코드를 받아 쓰기 | **이 저장소** |
| 파이썬으로 직접 호출해 보기 | [open-api](https://github.com/meritz-securities/open-api) — 실행 예제 |
| 터미널에서 조회·주문하기 | [open-api-studio](https://github.com/meritz-securities/open-api-studio) — `meritz` CLI |
| Claude 같은 AI에 붙이기 | [open-api-mcp](https://github.com/meritz-securities/open-api-mcp) — MCP 서버 |

## 설치 — 쓰시는 도구를 고르십시오

**Python이나 uv를 따로 깔지 않으셔도 됩니다.** 서버가 단일 실행 파일로 제공됩니다. 앱키도 필요 없습니다.

### Claude Desktop — 설치 파일 더블클릭

| 내 컴퓨터 | 내려받기 |
|---|---|
| Mac — Apple 칩 (M1 이후) | [**meritz-open-api-codegen-darwin-arm64.mcpb**](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen-darwin-arm64.mcpb) |
| Mac — Intel 칩 | [**meritz-open-api-codegen-darwin-x64.mcpb**](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen-darwin-x64.mcpb) |
| Windows | [**meritz-open-api-codegen-win32-x64.mcpb**](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen-win32-x64.mcpb) |

내려받은 파일을 더블클릭하고 설치를 누르시면 끝입니다.

- 어느 칩인지 모르시면 Mac은 Apple 메뉴 → 이 Mac에 관하여에서 "칩" 항목을 보세요.
- Mac에서 "확인되지 않은 개발자" 경고가 뜨면 시스템 설정 → 개인정보 보호 및 보안 → **그래도 열기**를 누르세요.
- 새 버전은 파일을 다시 내려받아 설치하십시오. 직접 내려받은 설치 파일은 자동으로 갱신되지 않습니다.


### 터미널로 설치하기 — `install.py`

포털 안내대로 저장소를 받아 `install.py`를 실행하면 이 PC에 맞는 실행 파일을 릴리스에서 내려받고, 클라이언트별로 붙여 넣을 명령을 보여 줍니다. Python은 이 스크립트를 돌리는 데만 쓰이고 실행 파일은 Python 없이 동작합니다.

```bash
git clone https://github.com/meritz-securities/open-api-codegen-mcp.git
cd open-api-codegen-mcp
python3 install.py                      # Windows: python install.py
python3 install.py --register claude-code   # Claude Code에 바로 등록 (codex · gemini 도 됩니다)
```

Mac 에서는 실행 권한 부여와 격리 속성(`com.apple.quarantine`) 해제까지 이 스크립트가 대신 해 줍니다. 아래 "실행 파일 + 명령 한 줄"을 손으로 하실 때만 두 단계를 직접 하시면 됩니다.

### Claude Code · Codex CLI · Gemini CLI · ChatGPT Desktop · Cursor · VS Code — 실행 파일 + 명령 한 줄

1. 실행 파일을 내려받아 원하는 곳에 둡니다.

   | 내 컴퓨터 | 내려받기 |
   |---|---|
   | Mac — Apple 칩 | [meritz-codegen-mcp-darwin-arm64](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-codegen-mcp-darwin-arm64) |
   | Mac — Intel 칩 | [meritz-codegen-mcp-darwin-x64](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-codegen-mcp-darwin-x64) |
   | Windows | [meritz-codegen-mcp-win32-x64.exe](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-codegen-mcp-win32-x64.exe) |

   **Mac 에서는 실행 권한과 격리 속성 해제를 둘 다 해 주셔야 합니다.** 한 번만 하시면 됩니다.

   ```bash
   chmod +x ~/Downloads/meritz-codegen-mcp-darwin-arm64
   xattr -d com.apple.quarantine ~/Downloads/meritz-codegen-mcp-darwin-arm64
   mkdir -p ~/meritz && mv ~/Downloads/meritz-codegen-mcp-darwin-arm64 ~/meritz/meritz-codegen-mcp
   ```

   > **격리 해제를 건너뛰면 서버가 뜨지 않습니다.** 브라우저로 내려받은 파일에는 macOS 가
   > `com.apple.quarantine` 속성을 붙입니다. 이 실행 파일은 ad-hoc 서명이라 Apple 개발자
   > 인증서가 없고 공증도 되어 있지 않아, 속성이 붙은 채로 실행되면 **아무 메시지 없이
   > 종료코드 -9(SIGKILL)로 죽습니다.** AI 앱의 도구 목록에 메리츠가 보이지 않는다면 이 속성이
   > 남아 있을 가능성이 큽니다. 같은 파일에서 속성만 지우면 정상 동작합니다.
   > `install.py` 로 설치하시면 실행 권한 부여와 격리 해제를 스크립트가 대신 해 줍니다.
   > (Claude Desktop 용 `.mcpb` 더블클릭은 Claude Desktop 이 직접 압축을 풀기 때문에
   > 이 속성이 붙지 않아, 이 작업이 필요 없습니다.)

   > **Windows** — `.exe` 를 처음 실행할 때 SmartScreen 경고가 뜰 수 있습니다. 서명되지 않은
   > 실행 파일이라 표시되는 경고입니다. 경고 창의 **추가 정보 → 실행**을 누르시면 됩니다.

2. 쓰시는 도구에 한 줄로 등록합니다. `<실행 파일 경로>`는 위에서 둔 위치의 **전체 경로**입니다.

   | 도구 | 명령 |
   |---|---|
   | **Claude Code** | `claude mcp add meritz-codegen -- <실행 파일 경로>` |
   | **Codex CLI** | `codex mcp add meritz-codegen -- <실행 파일 경로>` |
   | **Gemini CLI** | `gemini mcp add meritz-codegen <실행 파일 경로>` |
   | **ChatGPT Desktop** | 설정 → MCP servers → Add server → 이름 입력 → **STDIO** 선택 → 실행 파일 경로 입력 → 저장 → Restart |
   | **Cursor · VS Code** | 아래 JSON 설정을 각 앱의 MCP 설정 파일에 넣으십시오 |

   **ChatGPT Desktop을 쓰실 때** — 이 서버는 앱키가 필요 없으니 환경변수 없이 실행 파일 경로만 넣으시면 됩니다.
   ChatGPT 데스크톱 앱·Codex CLI·IDE 확장은 `~/.codex/config.toml`을 함께 씁니다. 한 곳에 등록하면 셋 다 잡힙니다.
   **ChatGPT 웹은 로컬 설정 파일을 읽지 못해 이 방식이 지원되지 않습니다** — 아래 터널 연결을 보십시오.

   **기동 대기는 60초로 늘려 두십시오.** 첫 기동에 8초 남짓 걸립니다(실측 8.2·8.2·8.6초).
   Codex·ChatGPT 데스크톱의 기본 대기는 10초라 여유가 2초도 되지 않아, 느린 PC 나 백신 검사가
   끼면 넘겨 도구가 아예 뜨지 않습니다. `~/.codex/config.toml` 의 `[mcp_servers.meritz-codegen]`
   테이블에 `startup_timeout_sec = 60` 한 줄을 넣어 주세요.

   ```toml
   [mcp_servers.meritz-codegen]
   command = "C:\\Users\\홍길동\\meritz\\meritz-codegen-mcp.exe"
   startup_timeout_sec = 60
   ```

<details>
<summary>uv와 Python 3.11 이상이 이미 있으시면 — 내려받기 없이 한 번에</summary>

| 도구 | 방법 |
|---|---|
| **Claude Desktop** | [meritz-open-api-codegen.mcpb](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen.mcpb) → 더블클릭 (파이썬·uv 필요. 다음 릴리스부터는 올라오지 않습니다) |
| **Claude Code** | `claude mcp add meritz-codegen -- uvx --from git+https://github.com/meritz-securities/open-api-codegen-mcp meritz-codegen-mcp` |
| **Cursor** | [**한 번에 추가**](cursor://anysphere.cursor-deeplink/mcp/install?name=meritz-codegen&config=eyJjb21tYW5kIjoidXZ4IiwiYXJncyI6WyItLWZyb20iLCJnaXQraHR0cHM6Ly9naXRodWIuY29tL21lcml0ei1zZWN1cml0aWVzL29wZW4tYXBpLWNvZGVnZW4tbWNwIiwibWVyaXR6LWNvZGVnZW4tbWNwIl19) |
| **VS Code** | [**한 번에 추가**](vscode:mcp/install?%7B%22name%22%3A%22meritz-codegen%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22--from%22%2C%22git%2Bhttps%3A//github.com/meritz-securities/open-api-codegen-mcp%22%2C%22meritz-codegen-mcp%22%5D%7D) |
| **Codex CLI** | `codex mcp add meritz-codegen -- uvx --from git+https://github.com/meritz-securities/open-api-codegen-mcp meritz-codegen-mcp` |

</details>

<details>
<summary>설정을 직접 넣으시려면</summary>

Codex CLI 는 `~/.codex/config.toml` 을 씁니다.

```toml
[mcp_servers.meritz-codegen]
command = "/Users/홍길동/meritz/meritz-codegen-mcp"
startup_timeout_sec = 60
```

그 밖의 도구는 대개 이 JSON 형식을 받습니다 (Claude Desktop `claude_desktop_config.json`, Cursor `mcp.json`, Gemini CLI `settings.json`).

```json
{
  "mcpServers": {
    "meritz-codegen": {
      "command": "/Users/홍길동/meritz/meritz-codegen-mcp"
    }
  }
}
```

</details>

### 릴리스에 올라온 파일이 무엇인지

[릴리스 페이지](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest)에는 파일이 여덟 개 있습니다. 쓰시는 것 **하나만** 받으시면 됩니다.

| 파일 | 무엇인지 |
|---|---|
| `meritz-open-api-codegen-darwin-arm64.mcpb`<br>`meritz-open-api-codegen-darwin-x64.mcpb`<br>`meritz-open-api-codegen-win32-x64.mcpb` | **Claude Desktop 설치 파일** (OS별 3종, 30MB 안팎). 더블클릭하면 설치됩니다 |
| `meritz-codegen-mcp-darwin-arm64`<br>`meritz-codegen-mcp-darwin-x64`<br>`meritz-codegen-mcp-win32-x64.exe` | **실행 파일** (OS별 3종, 30MB 안팎). Claude Code·Codex CLI·ChatGPT 데스크톱·Gemini CLI·Cursor·VS Code 에 **경로로 등록**해서 씁니다 |
| `SHA256SUMS.txt` | 위 파일들의 체크섬 |
| `meritz-open-api-codegen.mcpb` (100KB대) | **예전 방식입니다. 새로 받으실 분은 고르지 마십시오.** 실행 파일이 들어 있지 않고 uvx 로 내려받아 실행하는 형태라, **파이썬과 uv 가 따로 깔려 있어야** 동작합니다. 다음 릴리스부터는 올라오지 않습니다 |

받은 파일이 올라온 그대로인지 확인하시려면 `SHA256SUMS.txt` 를 받은 파일과 같은 폴더에 두고:

```bash
shasum -a 256 -c SHA256SUMS.txt                # 내려받지 않은 파일은 "FAILED open or read" 로 나옵니다
shasum -a 256 meritz-codegen-mcp-darwin-arm64  # 값 하나만 뽑아 SHA256SUMS.txt 의 해당 줄과 눈으로 대조하셔도 됩니다
```

Windows(PowerShell)에서는 값을 뽑아 대조하십시오.

```powershell
Get-FileHash .\meritz-codegen-mcp-win32-x64.exe -Algorithm SHA256
```

### Claude 웹·모바일, ChatGPT 웹 — 내 PC의 서버를 터널로 연결

두 서비스는 인터넷 주소(HTTPS)로 접근되는 MCP 서버만 받습니다. 이 서버를 HTTP 모드로 띄우고
터널 도구로 임시 주소를 만들면 붙일 수 있습니다. 앱키가 없는 서버라 노출 위험은 작지만,
그래도 난수 경로를 넣어 두십시오. PC를 켜 두어야 하고 무료 터널은 주소가 매번 바뀝니다.

```bash
MCP_TYPE=streamable-http MCP_PORT=8766 MCP_PATH=/mcp/<난수> ~/meritz/meritz-codegen-mcp   # 터미널 1
cloudflared tunnel --url http://127.0.0.1:8766                                          # 터미널 2 (또는 ngrok http 8766)
```

커넥터에 넣을 주소는 `https://<터널 주소>/mcp/<난수>` 입니다.
Claude는 설정 → 커넥터 → 커스텀 커넥터 추가(전 요금제), ChatGPT는 설정 → 커넥터 → 고급 → 개발자 모드 → 만들기(유료 요금제, 웹에서 설정)입니다. 인증은 비워 둡니다.

## 도구

| 도구 | 하는 일 |
|---|---|
| `list_categories()` | 분류와 건수 |
| `search_api(keyword, category)` | 자연어 검색. 한글 표현도 알아듣습니다 |
| `get_api_detail(api_type)` | 경로·파라미터·응답 필드·주의사항 |
| `generate_code(api_type)` | 호출 코드 (REST·실시간) |
| `api_conventions()` | 인증·호출 규약·응답 코드 |

이렇게 쓰시면 됩니다.

```
search_api("삼성전자 현재가")
search_api("해외 주문 취소")
generate_code("market_prices")
```

REST 62건과 실시간 13건 전부를 다룹니다. 카탈로그는 개발자 포털 등록 명세에서 만듭니다.

## 어떤 코드를 만들어 드리나요

- 토큰 발급·재사용, 요청, **응답 판정**까지 들어갑니다. HTTP 200만 보고 넘기지 않습니다
- 연속 조회(`rsp_cd`=`5762`)로 다음 페이지를 받는 방법을 주석으로 적어 드립니다
- 실시간은 웹소켓 구독 코드를 만들어 드립니다. 접속점은 하나이고 `tr_cd`가 무엇을 받을지 정합니다

### 주문 코드에는 확인 단계가 들어갑니다

주문·환전 코드는 `confirm=True`를 넘기기 전까지 전송하지 않는 형태로 만듭니다.
**그 단계를 지우고 쓰시면 확인 없이 전송됩니다.** 남겨 두시길 권합니다.

경고 확인 흐름도 함께 들어갑니다. 주문 응답이 성공(`rsp_cd`=`0001`)으로 와도
`data.warn_cls_code`가 `0`이 아니면 아직 접수되지 않은 상태라, 생성된 코드가
`MeritzWarning`을 던지고 `warn_cnfr_yn="A"`로 다시 보내야 한다는 것을 알려 줍니다.
재전송으로 접수되는 값은 **국내가 `1`·`3`·`4`·`6`·`7`·`9`·`a`·`c`·`d`·`f`·`g`,
해외는 `1`·`3` 둘뿐**이라 체계가 다릅니다. 코드를 국내·해외 공용으로 쓰지 마십시오.
이 검사는 `rsp_cd` 성공 반환보다 **앞에** 놓입니다. 뒤에 두면 걸리지 않기 때문입니다.

생성된 코드의 기본 대상은 **운영 서버**입니다. 실행 전에 요청 내용을 꼭 확인해 주세요.

## 포털 예시가 실제와 다를 때

명세는 포털에 등록된 내용을 그대로 따릅니다. 다만 포털 등록 내용과 실제 호출이
다른 API가 있습니다 — 예시대로 보내면 실패하거나, 오류 없이 0건이 내려오거나,
응답 코드가 손상되어 오는 경우입니다.

그런 API는 **실제로 동작하는 값으로 코드를 만들고**, 무엇이 다른지 코드 머리말에
적어 드립니다. 해당 목록은 `meritz_codegen/data/corrections.json`에 있고,
포털이 이미 고친 항목은 같은 파일의 `resolved`로 옮겨 둡니다.

## 오류 코드

이 게이트웨이는 **오류를 종류와 무관하게 HTTP 500으로** 냅니다. 상태코드로 가르지
마시고 본문의 `rsp_cd`를 읽으십시오. 무엇을 고쳐야 하는지는 `rsp_msg`가 아니라
`rsp_sub_msg`에 담겨 오므로, 생성된 코드는 오류 메시지에 두 값을 함께 싣습니다.

또 `rsp_cd`가 `5820`이라고 해서 자료가 없는 것이 아닙니다 — 담보 조회·종목별
실현손익·해외 실현손익은 자료를 담은 채로도 `5820`을 보냅니다.
**자료 유무는 `data`가 비었는지로 판정합니다.**

코드표는 [open-api 저장소의 docs/errors.md](https://github.com/meritz-securities/open-api/blob/main/docs/errors.md)에 있습니다.

## 개발

```bash
uv sync
uv run pytest tests/ -q
```

실행 파일과 설치 파일을 직접 만드시려면:

```bash
./build_binary.sh                    # bin/meritz-codegen-mcp — PyInstaller 단일 실행 파일, 자기 점검 포함
python3 make_bundle.py darwin-arm64  # dist/meritz-open-api-codegen-darwin-arm64.mcpb (darwin-x64 · win32-x64 도 같음)
./build_mcpb.sh                      # dist/meritz-open-api-codegen.mcpb — uv 로 실행하는 기존 방식
```

릴리스는 태그를 밀면 GitHub Actions가 세 플랫폼을 빌드해 올립니다: `git tag v0.3.0 && git push origin v0.3.0`.

## 함께 읽어 주십시오

- [DISCLAIMER.md](DISCLAIMER.md) — 생성된 코드를 실행하기 전에 확인하실 것
- [CONTRIBUTING.md](CONTRIBUTING.md) — 이슈·기여 방법
- [SECURITY.md](SECURITY.md) — 취약점 제보와 자격증명 취급

## 라이선스

MIT — [LICENSE](LICENSE)

문의는 [개발자 포털](https://openapi.imeritz.com)을 이용해 주세요.
