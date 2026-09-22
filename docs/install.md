# 설치

[README](../README.md) 의 설치 표로 대부분 끝납니다. 이 문서는 막힐 때 보는 절차입니다 —
OS 보안 경고, 기동 대기, 체크섬 대조, 설정 파일 직접 편집.

이 서버는 API 를 호출하지 않고 네트워크로 나가지 않습니다. 앱키가 필요 없습니다.

## Claude Desktop — `.mcpb` 더블클릭

| 플랫폼 | 파일 |
|---|---|
| macOS · Apple 실리콘 | [meritz-open-api-codegen-darwin-arm64.mcpb](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen-darwin-arm64.mcpb) |
| macOS · Intel | [meritz-open-api-codegen-darwin-x64.mcpb](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen-darwin-x64.mcpb) |
| Windows | [meritz-open-api-codegen-win32-x64.mcpb](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-open-api-codegen-win32-x64.mcpb) |

더블클릭하고 설치를 누르면 끝입니다. 입력할 값이 없습니다.

코드서명이 없어 macOS 는 "확인되지 않은 개발자" 경고를 띄웁니다. 넘기기 전에 아래
"체크섬 대조"로 파일을 확인하고, 시스템 설정 → 개인정보 보호 및 보안 → 그래도 열기로
진행하십시오. 새 버전은 파일을 다시 받아 설치합니다. 자동 갱신되지 않습니다.

## `install.py` — 실행 파일 내려받기와 등록

```bash
git clone https://github.com/meritz-securities/open-api-codegen-mcp.git
cd open-api-codegen-mcp
python3 install.py                            # 내려받기 + 체크섬 대조 + 연결 방법 출력
python3 install.py --register claude-code     # codex · gemini 도 됩니다
```

하는 일: 이 PC 에 맞는 실행 파일을 릴리스에서 받아 `bin/` 에 두고, 릴리스의
`SHA256SUMS.txt` 와 대조하고, 실행 권한과 macOS 격리 속성 해제를 적용합니다.
Python 은 이 스크립트를 돌리는 데만 쓰입니다 — 실행 파일 자체는 Python 없이 동작합니다.

## 실행 파일을 직접 등록

| 플랫폼 | 파일 |
|---|---|
| macOS · Apple 실리콘 | [meritz-codegen-mcp-darwin-arm64](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-codegen-mcp-darwin-arm64) |
| macOS · Intel | [meritz-codegen-mcp-darwin-x64](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-codegen-mcp-darwin-x64) |
| Windows | [meritz-codegen-mcp-win32-x64.exe](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest/download/meritz-codegen-mcp-win32-x64.exe) |

macOS 에서는 실행 권한과 격리 속성 해제를 둘 다 해야 합니다.

```bash
chmod +x ~/Downloads/meritz-codegen-mcp-darwin-arm64
xattr -d com.apple.quarantine ~/Downloads/meritz-codegen-mcp-darwin-arm64
mkdir -p ~/meritz && mv ~/Downloads/meritz-codegen-mcp-darwin-arm64 ~/meritz/meritz-codegen-mcp
```

> **격리 속성을 지우지 않으면 서버가 뜨지 않습니다.** 브라우저로 받은 파일에는 macOS 가
> `com.apple.quarantine` 을 붙입니다. 이 실행 파일은 ad-hoc 서명이라 Apple 개발자 인증서가
> 없고 공증도 되어 있지 않아, 속성이 붙은 채로 실행되면 **아무 메시지 없이 종료코드
> -9(SIGKILL)로 죽습니다.** AI 클라이언트의 도구 목록에 보이지 않으면 이 속성이 남아 있을
> 가능성이 큽니다. 속성만 지우면 같은 파일이 정상 동작합니다. `install.py` 는 이 두 단계를
> 대신 합니다. Claude Desktop 의 `.mcpb` 는 Claude Desktop 이 직접 풀기 때문에 해당되지 않습니다.

> **Windows** — `.exe` 첫 실행에서 SmartScreen 경고가 뜹니다. 코드서명이 없어 표시되는
> 경고입니다. 넘기기 전에 체크섬을 대조하고, 경고 창의 추가 정보 → 실행으로 진행합니다.

등록 명령. `<경로>` 는 실행 파일의 전체 경로입니다.

| 클라이언트 | 명령 |
|---|---|
| Claude Code | `claude mcp add meritz-codegen -- <경로>` |
| Codex CLI | `codex mcp add meritz-codegen -- <경로>` |
| Gemini CLI | `gemini mcp add meritz-codegen <경로>` |
| ChatGPT 데스크톱 | 설정 → MCP servers → Add server → STDIO → 실행 파일 경로 → 저장 → 재시작 |
| Cursor · VS Code | 아래 JSON 설정을 각 앱의 MCP 설정 파일에 넣으십시오 |

> **기동 대기를 60초로 늘리십시오.** 실행 파일은 매 기동마다 자기 내용을 임시 폴더로 풀기
> 때문에 첫 응답까지 8초 남짓 걸립니다(macOS Apple 실리콘 실측 7.5초). Codex CLI 와 ChatGPT
> 데스크톱의 기본 대기는 10초라 여유가 없어, 느린 PC 나 백신 검사가 끼면 넘겨 도구가 아예
> 뜨지 않습니다. `~/.codex/config.toml` 의 `[mcp_servers.meritz-codegen]` 테이블에
> `startup_timeout_sec = 60` 을 넣으십시오.

> ChatGPT 데스크톱 앱·Codex CLI·IDE 확장은 `~/.codex/config.toml` 을 함께 씁니다. 한 곳에
> 등록하면 나머지에도 잡힙니다. ChatGPT 웹은 이 파일을 읽지 못합니다.

## 설정 파일을 직접 편집

Codex CLI — `~/.codex/config.toml`

```toml
[mcp_servers.meritz-codegen]
command = "/Users/hong/meritz/meritz-codegen-mcp"
startup_timeout_sec = 60
```

그 밖의 클라이언트 — Claude Desktop `claude_desktop_config.json`, Cursor `mcp.json`,
Gemini CLI `settings.json`

```json
{
  "mcpServers": {
    "meritz-codegen": {
      "command": "/Users/hong/meritz/meritz-codegen-mcp"
    }
  }
}
```

uv 와 Python 3.11 이상이 이미 있으면 내려받기 없이 소스에서 실행할 수 있습니다.

```bash
claude mcp add meritz-codegen -- uvx --from git+https://github.com/meritz-securities/open-api-codegen-mcp meritz-codegen-mcp
codex  mcp add meritz-codegen -- uvx --from git+https://github.com/meritz-securities/open-api-codegen-mcp meritz-codegen-mcp
```

## 릴리스 자산

[릴리스 페이지](https://github.com/meritz-securities/open-api-codegen-mcp/releases/latest)에
열한 개가 올라옵니다. 쓰는 것 하나만 받으면 됩니다.

| 파일 | 용도 |
|---|---|
| `meritz-open-api-codegen-{darwin-arm64,darwin-x64,win32-x64}.mcpb` | Claude Desktop 설치 파일 (30MB 안팎) |
| `meritz-codegen-mcp-{darwin-arm64,darwin-x64}` · `meritz-codegen-mcp-win32-x64.exe` | 실행 파일. 다른 클라이언트에 경로로 등록 (30MB 안팎) |
| `THIRD-PARTY-NOTICES-{darwin-arm64,darwin-x64,win32-x64}.txt` | 실행 파일에 들어간 오픈소스의 라이선스 전문 |
| `SHA256SUMS.txt` | 위 열 개의 체크섬 |
| `meritz-open-api-codegen.mcpb` (100KB대) | 예전 방식. 실행 파일이 들어 있지 않고 uvx 로 내려받아 실행하므로 Python 과 uv 가 따로 깔려 있어야 합니다. 다음 릴리스부터는 올라오지 않습니다 |

## 체크섬 대조

`SHA256SUMS.txt` 를 받은 파일과 같은 폴더에 두고 대조합니다.

```bash
shasum -a 256 --ignore-missing -c SHA256SUMS.txt
```

```powershell
Get-FileHash .\meritz-codegen-mcp-win32-x64.exe -Algorithm SHA256
```

`install.py` 로 설치하면 이 대조를 자동으로 하고, 값이 다르면 받은 파일을 지우고 중단합니다.

## Claude 웹·모바일, ChatGPT 웹 — 터널

Claude 웹·모바일과 ChatGPT 웹은 HTTPS 주소로 접근되는 MCP 서버만 받습니다. 이 서버를 HTTP
모드로 띄우고 터널로 임시 주소를 만들면 붙일 수 있습니다.

이 서버는 앱키를 받지 않고 계좌에 접근하지 않습니다. 주소가 노출되어도 상대가 얻는 것은
공개 API 명세와 생성된 코드뿐입니다. 그래도 주소에는 난수 경로를 두십시오.

```bash
MCP_TYPE=streamable-http MCP_PORT=8766 MCP_PATH=/mcp/<난수> ~/meritz/meritz-codegen-mcp   # 터미널 1
cloudflared tunnel --url http://127.0.0.1:8766                                          # 터미널 2 (또는 ngrok http 8766)
```

`<난수>` 는 `openssl rand -hex 16` 으로 만듭니다. 커넥터에 넣을 주소는
`https://<터널 주소>/mcp/<난수>` 이고 인증은 비워 둡니다. Claude 는 설정 → 커넥터 →
커스텀 커넥터 추가, ChatGPT 웹은 설정 → 커넥터 → 고급 → 개발자 모드 → 만들기입니다.

PC 를 끄거나 터널을 닫으면 연결이 끊깁니다. 다시 열면 주소가 바뀌므로 커넥터도 다시
등록해야 합니다.
