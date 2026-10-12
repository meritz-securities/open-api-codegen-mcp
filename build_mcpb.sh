#!/usr/bin/env bash
# Claude Desktop 설치 파일(.mcpb)을 만듭니다.
#
#   ./build_mcpb.sh
#   → dist/<이름>.mcpb
#
# 이용자는 이 파일을 내려받아 더블클릭하면 됩니다. 설정 파일을 손댈 필요가 없습니다.
# 이 서버는 API 를 호출하지 않아 자격증명이 필요 없습니다.
set -euo pipefail
cd "$(dirname "$0")"
# 릴리스 자산 이름은 README 의 내려받기 링크와 같아야 한다.
# 폴더 이름을 쓰면 링크가 404 가 된다.
NAME=$(node -p "require('./manifest.json').name")

command -v npx >/dev/null || { echo "npx 가 필요합니다 (Node.js)"; exit 1; }

npx --yes @anthropic-ai/mcpb validate manifest.json
rm -rf dist
npx --yes @anthropic-ai/mcpb pack . "dist/$NAME.mcpb"

echo
echo "만들어진 파일: dist/$NAME.mcpb"
unzip -l "dist/$NAME.mcpb" | tail -1
