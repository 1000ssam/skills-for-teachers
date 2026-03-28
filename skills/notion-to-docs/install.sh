#!/bin/bash
# notion-to-docs 설치 스크립트 (macOS / Linux / WSL)
# 사용법: 터미널에서 아래 명령어 실행
#   curl -fsSL https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/notion-to-docs/install.sh | bash

set -e

REPO="1000ssam/skills-for-teachers"
BRANCH="main"
SKILL_NAME="notion-to-docs"
ZIP_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.zip"
TMP_DIR="$(mktemp -d)"
SKILLS_DIR="$HOME/.claude/skills"

echo ""
echo "📂 notion-to-docs 설치 중..."
echo ""

# 1. .claude/skills 폴더 생성
mkdir -p "$SKILLS_DIR"

# 2. ZIP 다운로드
echo "📥 다운로드 중..."
if ! curl -fsSL "$ZIP_URL" -o "$TMP_DIR/skills.zip"; then
    echo ""
    echo "❌ 다운로드 실패. 인터넷 연결을 확인해 주세요."
    rm -rf "$TMP_DIR"
    exit 1
fi

# 3. 압축 해제
unzip -qo "$TMP_DIR/skills.zip" -d "$TMP_DIR"

# 4. 스킬 복사 (기존 config.json, token.json 보존)
SRC="$TMP_DIR/skills-for-teachers-$BRANCH/skills/$SKILL_NAME"
DST="$SKILLS_DIR/$SKILL_NAME"

if [ -d "$DST" ]; then
    # 기존 설치: config.json, token.json 백업
    [ -f "$DST/config.json" ] && cp "$DST/config.json" "$TMP_DIR/config.json.bak"
    [ -f "$DST/token.json" ] && cp "$DST/token.json" "$TMP_DIR/token.json.bak"
fi

cp -rf "$SRC" "$DST"

# 백업 복원
[ -f "$TMP_DIR/config.json.bak" ] && cp "$TMP_DIR/config.json.bak" "$DST/config.json"
[ -f "$TMP_DIR/token.json.bak" ] && cp "$TMP_DIR/token.json.bak" "$DST/token.json"

# 5. 임시 파일 정리
rm -rf "$TMP_DIR"

echo ""
echo "✅ 설치 완료!"
echo ""
echo "다음 단계:"
echo "  1. Notion Integration 토큰을 준비하세요"
echo "     https://www.notion.so/profile/integrations → '새 API 통합' → 토큰 복사"
echo "  2. Claude Code를 재시작한 뒤 이렇게 말해보세요:"
echo '     "노션 문서 변환해줘"'
echo "     (처음 실행 시 Notion 토큰 + Google 로그인을 안내합니다)"
echo ""
echo "⚠️  Node.js 18 이상이 필요합니다: https://nodejs.org"
echo ""
