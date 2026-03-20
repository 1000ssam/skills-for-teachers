# skills-for-teachers 전체 설치 스크립트 (Windows)
# 사용법: 터미널에서 아래 명령어 실행
#   irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/install.ps1 | iex

$ErrorActionPreference = 'Stop'

$repo     = "1000ssam/skills-for-teachers"
$branch   = "main"
$zipUrl   = "https://github.com/$repo/archive/refs/heads/$branch.zip"
$zipPath  = "$env:TEMP\skills-for-teachers.zip"
$extPath  = "$env:TEMP\skills-for-teachers-extract"
$skillsDir = "$env:USERPROFILE\.claude\skills"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  선생님용 Claude 스킬 설치 프로그램" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 1. .claude\skills 폴더 생성
if (-not (Test-Path $skillsDir)) {
    New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
    Write-Host "📁 스킬 폴더를 새로 만들었습니다: $skillsDir" -ForegroundColor Yellow
}

# 2. ZIP 다운로드
Write-Host "📥 스킬 파일 다운로드 중..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
} catch {
    Write-Host ""
    Write-Host "❌ 다운로드 실패. 인터넷 연결을 확인해 주세요." -ForegroundColor Red
    Write-Host "   오류: $_" -ForegroundColor Red
    exit 1
}

# 3. 압축 해제
if (Test-Path $extPath) { Remove-Item -Recurse -Force $extPath }
Expand-Archive -Path $zipPath -DestinationPath $extPath -Force

# 4. 스킬 복사
$sourceSkills = "$extPath\skills-for-teachers-$branch\skills"
$skills = @("document-organizer", "exam-analyzer", "handover-generator", "student-record-writer", "learn-claude-code", "notion-pilot")

Write-Host ""
foreach ($skill in $skills) {
    $src = "$sourceSkills\$skill"
    if (Test-Path $src) {
        $dst = "$skillsDir\$skill"
        Copy-Item -Recurse -Force $src $dst
        Write-Host "  ✅ $skill" -ForegroundColor Green
    }
}

# 5. 임시 파일 정리
Remove-Item -Force $zipPath -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $extPath -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "🎉 설치 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "이제 Claude Code를 재시작하면 스킬을 사용할 수 있습니다." -ForegroundColor White
Write-Host ""
Write-Host "사용 예시:" -ForegroundColor Cyan
Write-Host '  "공문서 정리해줘"          → document-organizer' -ForegroundColor Gray
Write-Host '  "인수인계서 작성해줘"       → handover-generator' -ForegroundColor Gray
Write-Host '  "기출 분석해줘"            → exam-analyzer' -ForegroundColor Gray
Write-Host '  "생기부 써줘"              → student-record-writer' -ForegroundColor Gray
Write-Host '  "Claude Code 배우고 싶어"  → learn-claude-code' -ForegroundColor Gray
Write-Host ""
