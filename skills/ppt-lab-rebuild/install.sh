#!/bin/bash
# ppt-lab-rebuild 설치 스크립트 (macOS / Linux)
# 사용법: 터미널에서 아래 명령어 실행
#   curl -fsSL https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/ppt-lab-rebuild/install.sh | bash

set -e

REPO="1000ssam/skills-for-teachers"
BRANCH="main"
SKILL="ppt-lab-rebuild"
ZIP_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.zip"
TMP_DIR="$(mktemp -d)"
SKILLS_DIR="$HOME/.claude/skills"

echo ""
echo "🎨 ppt-lab-rebuild 설치 중..."
echo ""

mkdir -p "$SKILLS_DIR"

echo "📥 다운로드 중..."
if ! curl -fsSL "$ZIP_URL" -o "$TMP_DIR/skills.zip"; then
    echo "❌ 다운로드 실패. 인터넷 연결을 확인해 주세요."
    rm -rf "$TMP_DIR"
    exit 1
fi

unzip -qo "$TMP_DIR/skills.zip" -d "$TMP_DIR"

SRC="$TMP_DIR/skills-for-teachers-$BRANCH/skills/$SKILL"
if [ -d "$SRC" ]; then
    cp -rf "$SRC" "$SKILLS_DIR/$SKILL"
    echo "  ✅ $SKILL"
fi

rm -rf "$TMP_DIR"

# Python 의존성
echo "🐍 Python 의존성 확인 중..."
if python3 -m pip install python-pptx pillow -q 2>/dev/null; then
    echo "  ✅ python-pptx, pillow"
else
    echo "  ⚠️  Python 패키지 자동 설치 실패 — 수동 설치 필요:"
    echo "     python3 -m pip install python-pptx pillow"
fi

echo ""
echo "🎉 설치 완료!"
echo ""
echo "Claude Code를 재시작한 뒤 사용하세요:"
echo '  "ppt-lab-rebuild 로 강의 자료 만들어줘"'
echo ""
echo "💡 미리보기 렌더는 PowerPoint 또는 LibreOffice가 필요합니다."
echo ""
