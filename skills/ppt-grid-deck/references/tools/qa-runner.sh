#!/usr/bin/env bash
# qa-runner.sh — PPTX QA 자동화 (ppt-deck skill)
#
# 한 줄로 4단계 자동 실행:
#   1) markitdown  → 콘텐츠 추출 · placeholder 잔여물 확인
#   2) soffice/PowerPoint → PPTX 를 슬라이드별 PNG 로 렌더 (시각 검토용)
#   3) subagent prompt 생성 → fresh-eye 시각 검토용 프롬프트 파일 출력
#
# 사용법:
#   bash qa-runner.sh /path/to/deck.pptx [look-slug]
#     · look-slug 를 주면 렌더 전에 그 룩이 쓰는 폰트를 자동 보장(없으면 다운로드·설치).
#
# 환경 적응:
#   - LibreOffice(soffice) 있으면 그걸로 PDF→PNG.
#   - 없고 Windows PowerPoint(WSL) 환경이면 PowerPoint COM 으로 PNG export.
#   - 둘 다 없으면 콘텐츠 QA 만 수행하고 시각 검토는 건너뜀.
set -uo pipefail

PPTX="${1:?usage: qa-runner.sh deck.pptx [look-slug]}"
[ -f "$PPTX" ] || { echo "❌ 파일 없음: $PPTX"; exit 1; }
LOOK="${2:-}"
TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PPTX_ABS="$(cd "$(dirname "$PPTX")" && pwd)/$(basename "$PPTX")"
BASE="$(basename "${PPTX%.*}")"
QADIR="$(dirname "$PPTX_ABS")/${BASE}_qa"
IMGDIR="$QADIR/images"
mkdir -p "$IMGDIR"

echo "════════════════════════════════════════"
echo "  ppt-deck QA · $BASE"
echo "════════════════════════════════════════"

# ── 1) 콘텐츠 QA (markitdown) ───────────────────────────
echo ""; echo "▶ 1. 콘텐츠 추출 + placeholder 체크 (markitdown)"
python3 - "$PPTX_ABS" "$QADIR/content.md" << 'PY'
import sys
from markitdown import MarkItDown
pptx, out = sys.argv[1], sys.argv[2]
t = MarkItDown().convert(pptx).text_content
open(out, "w", encoding="utf-8").write(t)
slides = t.count("<!-- Slide number:")
print(f"   슬라이드 {slides}장 · {len(t)}자 추출 → {out}")
bad = [p for p in ["undefined", "None", "{{", "}}", "lorem", "TODO", "PLACEHOLDER"]
       if p.lower() in t.lower()]
print("   ⚠ placeholder 잔여물:", bad if bad else "없음 ✅")
PY

# ── 1.5) 폰트 보장 (없으면 다운로드·설치) ──────────────
# 렌더(COM)·PowerPoint 가 폰트를 대체하지 않도록, 이 덱이 쓰는 폰트를 미리 보장한다.
# 룩 슬러그(2번째 인자)가 있을 때만 동작 — best-effort(실패해도 렌더는 계속). 멱등.
# ensure-fonts.ps1 은 WSL 네이티브 위치라 powershell.exe 에는 wslpath -w(UNC) 로 넘긴다.
if [ -n "$LOOK" ] && command -v powershell.exe >/dev/null 2>&1 && [ -f "$TOOLS_DIR/ensure-fonts.ps1" ]; then
  echo ""; echo "▶ 1.5 폰트 보장 (ensure-fonts -Look $LOOK)"
  EF_WIN="$(wslpath -w "$TOOLS_DIR/ensure-fonts.ps1" 2>/dev/null)"
  if [ -n "$EF_WIN" ]; then
    powershell.exe -ExecutionPolicy Bypass -File "$EF_WIN" -Look "$LOOK" 2>&1 \
      | grep -aiE "installed|download|설치|받|warn|fail" | head -8 || true
    echo "   (폰트 보장 완료 — 미해소분은 ensure-fonts.ps1 -All 또는 수동 설치)"
  fi
fi

# ── 2) 슬라이드 → PNG 렌더 ─────────────────────────────
echo ""; echo "▶ 2. 슬라이드 이미지 렌더"
RENDERED=0
if command -v soffice >/dev/null 2>&1; then
  echo "   LibreOffice 사용"
  soffice --headless --convert-to pdf --outdir "$QADIR" "$PPTX_ABS" >/dev/null 2>&1
  PDF="$QADIR/${BASE}.pdf"
  if [ -f "$PDF" ] && command -v pdftoppm >/dev/null 2>&1; then
    pdftoppm -png -r 96 "$PDF" "$IMGDIR/slide" >/dev/null 2>&1
    RENDERED=$(ls "$IMGDIR"/slide*.png 2>/dev/null | wc -l)
  fi
elif [ -f "/mnt/c/Program Files/Microsoft Office/root/Office16/POWERPNT.EXE" ] && command -v powershell.exe >/dev/null 2>&1; then
  echo "   Windows PowerPoint 사용"
  # 잔존 헤드리스(COM 자동화) PowerPoint 좀비가 임시/산출 .pptx 를 잡고 있으면
  # 이후 빌드가 PermissionError 로 막힌다. 창이 없는(MainWindowHandle==0) 것만
  # 정리해 사용자가 직접 연 PowerPoint(창 있음)는 절대 건드리지 않는다.
  powershell.exe -Command 'Get-Process POWERPNT -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -eq 0 } | Stop-Process -Force -ErrorAction SilentlyContinue' >/dev/null 2>&1
  # ⚠ 한글/공백 파일명 대응: powershell -File 은 .ps1 을 ANSI(CP949)로 읽어
  #   UTF-8 한글 경로를 깨뜨린다. 따라서 렌더는 ASCII 전용 임시 폴더에서 수행하고,
  #   .ps1 에는 ASCII 경로만 넣은 뒤 결과 PNG 만 bash 로 IMGDIR(한글 경로 가능)에 복사한다.
  WORK="/mnt/c/Users/$USER/AppData/Local/Temp/pptdeck_qa_$$"
  if ! mkdir -p "$WORK/out" 2>/dev/null; then
    WORK="$(dirname "$(mktemp -u)")/pptdeck_qa_$$"; mkdir -p "$WORK/out"
  fi
  cp "$PPTX_ABS" "$WORK/deck.pptx"
  WIN_WORK="$(wslpath -w "$WORK" 2>/dev/null || echo "C:\\Users\\$USER\\AppData\\Local\\Temp\\pptdeck_qa_$$")"
  PS1="$WORK/_export.ps1"
  printf '\xEF\xBB\xBF' > "$PS1"   # UTF-8 BOM → PowerShell 이 UTF-8 로 해석 (이중 안전장치)
  cat >> "$PS1" << PSEOF
\$ErrorActionPreference="Stop"
\$ppt=New-Object -ComObject PowerPoint.Application
\$p=\$ppt.Presentations.Open("$WIN_WORK\\deck.pptx",\$true,\$false,\$false)
for(\$i=1;\$i -le \$p.Slides.Count;\$i++){ \$p.Slides.Item(\$i).Export("$WIN_WORK\\out\\slide_\$i.png","PNG",1920,1080) }
\$p.Close(); \$ppt.Quit()
[System.Runtime.InteropServices.Marshal]::ReleaseComObject(\$p) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject(\$ppt) | Out-Null
[GC]::Collect(); [GC]::WaitForPendingFinalizers()
PSEOF
  powershell.exe -ExecutionPolicy Bypass -File "$WIN_WORK\\_export.ps1" >/dev/null 2>&1
  cp "$WORK/out/"slide_*.png "$IMGDIR/" 2>/dev/null   # bash cp 는 UTF-8 경로 안전
  RENDERED=$(find "$IMGDIR" -iname '*.png' 2>/dev/null | wc -l)
  rm -rf "$WORK" 2>/dev/null
else
  echo "   ⚠ soffice/PowerPoint 없음 → 시각 렌더 건너뜀 (콘텐츠 QA 만 수행)"
fi
echo "   렌더된 이미지: ${RENDERED}장 → $IMGDIR"

# ── 3) subagent 시각검토 프롬프트 생성 ──────────────────
echo ""; echo "▶ 3. subagent 시각검토 프롬프트 생성"
PROMPT="$QADIR/subagent-prompt.md"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cat > "$PROMPT" << EOF
# Fresh-eye 시각 검토 요청

아래 슬라이드 이미지들을 **처음 보는 사람** 관점에서 검토하세요.
이미지 경로: $IMGDIR  (slide*.png)
금지 패턴 기준: $SKILL_DIR/forbidden-patterns.md

각 슬라이드마다 확인:
1. AI tell 12종 위반 (제목 밑 액센트바 / 본문 중앙정렬 / emoji / 텍스트전용 / 모티프 불일치 등)
2. 텍스트 잘림·오버플로우·여백 침범
3. 차트 라벨 누락·축 깨짐
4. 팔레트 일관성 (한 덱 = 한 톤)
5. 카피 규칙 위반 (불릿 줄글, 숫자 단위 누락)

출력: 슬라이드 번호별 이슈 목록 + 심각도(blocker/minor) + 수정 제안.
이슈 0건이면 "QA PASS" 선언.
EOF
echo "   → $PROMPT"

echo ""; echo "════════════════════════════════════════"
echo "  QA 산출물: $QADIR"
echo "  다음: 위 subagent-prompt.md 로 Agent 호출 → 이슈 0개까지 수정·재빌드 반복"
echo "════════════════════════════════════════"
