#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""메리츠증권 Open API — 코드 생성 MCP 설치 도우미.

포털 안내(git clone → python3 install.py)와 호환되도록 남겨 둔 파일입니다.
하는 일: 이 PC에 맞는 실행 파일을 GitHub 릴리스에서 받아 bin/ 에 두고,
AI 클라이언트별로 붙여 넣을 명령을 보여 줍니다. Python 은 이 스크립트를 돌리는 데만 쓰이고
실행 파일 자체는 Python 없이 동작합니다.

    python3 install.py                 # 실행 파일 내려받기 + 연결 명령 안내
    python3 install.py --register claude-code   # Claude Code 에 바로 등록
    python3 install.py --register codex         # Codex CLI 에 바로 등록
    python3 install.py --register gemini        # Gemini CLI 에 바로 등록
"""
import os, platform, shutil, stat, subprocess, sys, urllib.request

REPO = "meritz-securities/open-api-codegen-mcp"
ASSET_PREFIX = "meritz-codegen-mcp"            # 릴리스 자산 이름 앞부분
SERVER_NAME = "meritz-codegen"            # 클라이언트에 등록되는 서버 이름
MCPB = "meritz-open-api-codegen"                     # Claude Desktop 설치 파일 이름 앞부분

def target():
    s, m = platform.system(), platform.machine().lower()
    if s == "Darwin":  return ("darwin-arm64" if m in ("arm64", "aarch64") else "darwin-x64"), ""
    if s == "Windows": return "win32-x64", ".exe"
    sys.exit("지원하지 않는 OS 입니다: %s. 소스 실행은 README 의 uv 방식을 보십시오." % s)

def download(url, dst):
    try:
        with urllib.request.urlopen(url, timeout=60) as r, open(dst, "wb") as f:
            shutil.copyfileobj(r, f)
        return True
    except Exception as e:
        # 비공개 저장소이거나 네트워크 제한이면 gh CLI 로 시도한다
        if shutil.which("gh"):
            name = url.rsplit("/", 1)[-1]
            r = subprocess.run(["gh", "release", "download", "--repo", REPO, "--pattern", name, "--output", dst, "--clobber"])
            return r.returncode == 0
        print("내려받기 실패: %s" % e)
        return False

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    plat, ext = target()
    name = "%s-%s%s" % (ASSET_PREFIX, plat, ext)
    url = "https://github.com/%s/releases/latest/download/%s" % (REPO, name)
    os.makedirs(os.path.join(here, "bin"), exist_ok=True)
    dst = os.path.join(here, "bin", name)
    print("실행 파일 내려받는 중: %s" % url)
    if not download(url, dst):
        sys.exit("실행 파일을 받지 못했습니다. 브라우저에서 위 주소를 직접 열어 bin/ 폴더에 저장한 뒤 다시 실행하십시오.")
    if ext == "":
        os.chmod(dst, os.stat(dst).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        subprocess.run(["xattr", "-d", "com.apple.quarantine", dst], capture_output=True)  # Mac 격리 속성 제거
    print("완료: %s\n" % dst)

    # 이 서버는 API 를 호출하지 않아 자격증명이 필요 없다. 경로만 넘긴다.
    cmds = {
        "claude-code": "claude mcp add %s -- \"%s\"" % (SERVER_NAME, dst),
        "codex":       "codex mcp add %s -- \"%s\"" % (SERVER_NAME, dst),
        "gemini":      "gemini mcp add %s \"%s\"" % (SERVER_NAME, dst),
    }
    reg = None
    if "--register" in sys.argv:
        i = sys.argv.index("--register"); reg = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
    if reg in cmds:
        print("등록 실행: %s" % cmds[reg])
        r = subprocess.run(cmds[reg], shell=True)
        sys.exit(r.returncode)

    print("AI 클라이언트에 연결하는 방법 — 쓰는 것 하나만 하시면 됩니다.\n")
    print("  Claude Desktop : 설치 파일을 내려받아 더블클릭")
    print("                   https://github.com/%s/releases/latest/download/%s-%s.mcpb\n" % (REPO, MCPB, plat))
    print("  Claude Code    : %s" % cmds["claude-code"])
    print("  Codex CLI      : %s" % cmds["codex"])
    print("  Gemini CLI     : %s" % cmds["gemini"])
    print("  Cursor·VS Code : README 의 '한 번에 추가' 버튼")
    print("  ChatGPT Desktop: 설정 → MCP servers → Add server → STDIO → 실행 파일 경로 입력 → 저장 → 재시작")
    print("\n  이 서버는 API 를 호출하지 않아 앱키가 필요 없습니다. 경로만 넣으시면 됩니다.")
    print("\n연결 후 AI 클라이언트를 완전히 종료했다가 다시 실행하십시오.")

if __name__ == "__main__":
    main()
