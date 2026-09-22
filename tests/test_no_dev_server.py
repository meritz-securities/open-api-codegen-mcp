"""공개 저장소에 운영이 아닌 서버의 흔적이 남지 않았는지 지킨다.

생성된 코드가 운영 서버를 향하는지는 tests/test_codegen.py 가 본다.
여기서는 그보다 앞선 것을 본다 — **커밋된 파일 어디에도** 운영이 아닌 서버 주소가
없어야 한다. 카탈로그·명세·문서·빌드 스크립트 중 하나에라도 남으면
배포 실행 파일에 그대로 실려 나가기 때문이다.

검사 문자열은 이 파일 자신이 걸리지 않도록 쪼개 두었다.
"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()
sys.path.insert(0, str(ROOT))

# "dev" + "api" — 한 조각으로 적으면 이 파일이 스스로 걸린다.
FORBIDDEN = "dev" + "api"

# 텍스트로 읽지 않는 것들. 이진 파일은 어차피 decode 에서 걸러진다.
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".mcpb"}


def tracked_files():
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [ROOT / name for name in out.split("\0") if name]


class NoDevServerTest(unittest.TestCase):
    def test_repository_has_no_dev_server_reference(self):
        files = tracked_files()
        self.assertTrue(files, "git ls-files 가 비었습니다. 저장소 안에서 돌려 주십시오.")

        hits = []
        for path in files:
            if path.resolve() == SELF or path.suffix.lower() in SKIP_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                if FORBIDDEN in line.lower():
                    rel = path.relative_to(ROOT)
                    hits.append(f"{rel}:{lineno}: {line.strip()[:120]}")

        self.assertEqual(
            [], hits,
            "운영이 아닌 서버 주소가 남아 있습니다. 운영 기준만 커밋해 주십시오:\n" + "\n".join(hits),
        )

    def test_catalog_domains_are_production_only(self):
        from meritz_codegen import load_catalog

        for api in load_catalog():
            domain = api["domain"]
            self.assertEqual(
                ["prod"], sorted(domain), f"{api.key}: domain 에 prod 외의 키가 있습니다",
            )
            self.assertIn("openapi.imeritz.com", domain["prod"], api.key)


if __name__ == "__main__":
    unittest.main()
