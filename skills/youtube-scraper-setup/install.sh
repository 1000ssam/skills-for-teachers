#!/bin/bash
# youtube-scraper-setup 설치 스크립트 (macOS / Linux)
# 사용법: 터미널에서 아래 명령어 실행
#   curl -fsSL https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/youtube-scraper-setup/install.sh | bash

set -e

REPO="1000ssam/skills-for-teachers"
BRANCH="main"
SKILL_NAME="youtube-scraper-setup"
ZIP_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.zip"
TMP_DIR="$(mktemp -d)"
SKILLS_DIR="$HOME/.claude/skills"

echo ""
echo "📂 youtube-scraper-setup 설치 중..."
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

# 4. 스킬 파일 복사 (SKILL.md → youtube-scraper-setup.md)
SRC="$TMP_DIR/skills-for-teachers-$BRANCH/skills/$SKILL_NAME/SKILL.md"
DST="$SKILLS_DIR/$SKILL_NAME.md"
cp -f "$SRC" "$DST"

# 5. 임시 파일 정리
rm -rf "$TMP_DIR"

echo ""
echo "✅ 설치 완료!"
echo ""
echo "다음 단계:"
echo "  1. Node.js v18 이상이 설치되어 있는지 확인하세요"
echo "     node --version"
echo "  2. yt-dlp가 설치되어 있는지 확인하세요"
echo "     pip install yt-dlp"
echo "  3. Notion Integration 토큰을 준비하세요"
echo "     https://www.notion.so/profile/integrations → '새 API 통합' → 토큰 복사"
echo "  4. Claude Code를 재시작한 뒤 이렇게 말해보세요:"
echo '     "유튜브 스크래퍼 만들어줘"'
echo ""
