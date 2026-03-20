#!/bin/bash
# skills-for-teachers 전체 설치 스크립트 (macOS / Linux)
# 사용법: 터미널에서 아래 명령어 실행
#   curl -fsSL https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/install.sh | bash

set -e

REPO="1000ssam/skills-for-teachers"
BRANCH="main"
ZIP_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.zip"
TMP_DIR="$(mktemp -d)"
SKILLS_DIR="$HOME/.claude/skills"

echo ""
echo "======================================"
echo "  선생님용 Claude 스킬 설치 프로그램"
echo "======================================"
echo ""

# 1. .claude/skills 폴더 생성
mkdir -p "$SKILLS_DIR"

# 2. ZIP 다운로드
echo "📥 스킬 파일 다운로드 중..."
if ! curl -fsSL "$ZIP_URL" -o "$TMP_DIR/skills.zip"; then
    echo ""
    echo "❌ 다운로드 실패. 인터넷 연결을 확인해 주세요."
    rm -rf "$TMP_DIR"
    exit 1
fi

# 3. 압축 해제
unzip -qo "$TMP_DIR/skills.zip" -d "$TMP_DIR"

# 4. 스킬 복사
SOURCE_SKILLS="$TMP_DIR/skills-for-teachers-$BRANCH/skills"
SKILLS=("document-organizer" "exam-analyzer" "handover-generator" "student-record-writer" "learn-claude-code" "notion-pilot")

echo ""
for skill in "${SKILLS[@]}"; do
    if [ -d "$SOURCE_SKILLS/$skill" ]; then
        cp -rf "$SOURCE_SKILLS/$skill" "$SKILLS_DIR/$skill"
        echo "  ✅ $skill"
    fi
done

# 5. 임시 파일 정리
rm -rf "$TMP_DIR"

echo ""
echo "🎉 설치 완료!"
echo ""
echo "이제 Claude Code를 재시작하면 스킬을 사용할 수 있습니다."
echo ""
echo "사용 예시:"
echo '  "공문서 정리해줘"          → document-organizer'
echo '  "인수인계서 작성해줘"       → handover-generator'
echo '  "기출 분석해줘"            → exam-analyzer'
echo '  "생기부 써줘"              → student-record-writer'
echo '  "Claude Code 배우고 싶어"  → learn-claude-code'
echo ""
