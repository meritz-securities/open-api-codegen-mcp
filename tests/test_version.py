"""판 번호가 세 곳에서 어긋나지 않는지 본다.

릴리스는 0.3.1 인데 서버가 자기를 0.3.0 이라고 답한 적이 있다. 사람이 세 파일을
같이 고쳐야 하는 구조였기 때문이다. 이제 __init__ 이 정본이고, 나머지 둘이
그것과 같은지 여기서 검사한다.
"""
from __future__ import annotations

import json
import pathlib
import re

from meritz_codegen import __version__

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_pyproject_matches_the_package_version():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    found = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    assert found and found.group(1) == __version__, \
        f'pyproject.toml 은 {found and found.group(1)}, 패키지는 {__version__}'


def test_manifest_matches_the_package_version():
    data = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert data["version"] == __version__, \
        f'manifest.json 은 {data["version"]}, 패키지는 {__version__}'


def test_server_reports_the_package_version():
    from meritz_codegen.server import mcp

    assert mcp.version == __version__


def test_manifest_declares_every_prompt_the_server_exposes():
    """Claude Desktop 은 manifest 에 선언되지 않은 프롬프트를 막는다.

    실제로 'attempted undeclared prompt' 로 거절당했다. 서버가 내놓는데
    번들이 선언하지 않으면 사용자에게는 "프롬프트 첨부 실패"로만 보인다.
    """
    import asyncio

    from meritz_codegen.server import mcp

    declared = {p["name"] for p in
                json.loads((ROOT / "manifest.json").read_text(encoding="utf-8")).get("prompts", [])}
    exposed = {p.name for p in asyncio.run(mcp.list_prompts())}
    assert exposed <= declared, f"manifest 에 없는 프롬프트: {sorted(exposed - declared)}"
    assert declared <= exposed, f"서버에 없는데 manifest 에만 있는 프롬프트: {sorted(declared - exposed)}"


def test_manifest_declares_every_tool_the_server_exposes():
    """도구도 같다. 선언과 구현이 어긋나면 일부만 보인다."""
    import asyncio

    from meritz_codegen.server import mcp

    declared = {t["name"] for t in
                json.loads((ROOT / "manifest.json").read_text(encoding="utf-8")).get("tools", [])}
    exposed = {t.name for t in asyncio.run(mcp.list_tools())}
    assert exposed == declared, (f"manifest 에 없는 도구: {sorted(exposed - declared)} / "
                                 f"서버에 없는 도구: {sorted(declared - exposed)}")


def test_manifest_prompt_entries_have_every_required_key():
    """mcpb validate 가 요구하는 키. 빠지면 릴리스 빌드가 통째로 멈춘다.

    prompts[].text 를 빠뜨려 실제로 빌드가 실패했다. 빌드까지 가서야 알게
    되는 것을 여기서 먼저 걸어 준다.
    """
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest.get("prompts", []):
        missing = {"name", "description", "arguments", "text"} - set(entry)
        assert not missing, f'prompts 항목 {entry.get("name")} 에 없는 키: {sorted(missing)}'
    for entry in manifest.get("tools", []):
        missing = {"name", "description"} - set(entry)
        assert not missing, f'tools 항목 {entry.get("name")} 에 없는 키: {sorted(missing)}'
