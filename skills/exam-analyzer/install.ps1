# exam-analyzer 설치 스크립트
# 사용법: PowerShell에서 아래 명령어 실행
#   irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/exam-analyzer/install.ps1 | iex

$ErrorActionPreference = 'Stop'

$repo      = "1000ssam/skills-for-teachers"
$branch    = "main"
$skillName = "exam-analyzer"
$zipUrl    = "https://github.com/$repo/archive/refs/heads/$branch.zip"
$zipPath   = "$env:TEMP\skills-for-teachers.zip"
$extPath   = "$env:TEMP\skills-for-teachers-extract"
$skillsDir = "$env:USERPROFILE\.claude\skills"

Write-Host ""
Write-Host "📊 exam-analyzer 설치 중..." -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $skillsDir)) {
    New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
}

Write-Host "📥 다운로드 중..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
} catch {
    Write-Host "❌ 다운로드 실패. 인터넷 연결을 확인해 주세요." -ForegroundColor Red
    exit 1
}

if (Test-Path $extPath) { Remove-Item -Recurse -Force $extPath }
Expand-Archive -Path $zipPath -DestinationPath $extPath -Force

$src = "$extPath\skills-for-teachers-$branch\skills\$skillName"
$dst = "$skillsDir\$skillName"
Copy-Item -Recurse -Force $src $dst

Remove-Item -Force $zipPath -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $extPath -ErrorAction SilentlyContinue

# Python 의존성 확인
Write-Host "🐍 Python 의존성 확인 중..." -ForegroundColor Yellow
try {
    python -m pip install pymupdf pillow numpy -q 2>$null
    Write-Host "  ✅ pymupdf, pillow, numpy" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Python 패키지 자동 설치 실패. 수동으로 설치해 주세요:" -ForegroundColor Yellow
    Write-Host "     pip install pymupdf pillow numpy" -ForegroundColor Gray
}

Write-Host ""
Write-Host "✅ 설치 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "Claude Code를 재시작한 뒤 이렇게 말해보세요:" -ForegroundColor White
Write-Host '  "기출 분석해줘"' -ForegroundColor Cyan
Write-Host '  "03단원 기출 정리"' -ForegroundColor Cyan
Write-Host ""
Write-Host "첫 실행 시 교과서 폴더와 기출 폴더 경로를 물어봅니다." -ForegroundColor Gray
Write-Host ""
