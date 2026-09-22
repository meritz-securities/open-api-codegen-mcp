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
