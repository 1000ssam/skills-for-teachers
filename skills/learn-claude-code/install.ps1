# learn-claude-code 설치 스크립트
# 사용법: PowerShell에서 아래 명령어 실행
#   irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/learn-claude-code/install.ps1 | iex

$ErrorActionPreference = 'Stop'

$repo      = "1000ssam/skills-for-teachers"
$branch    = "main"
$skillName = "learn-claude-code"
$zipUrl    = "https://github.com/$repo/archive/refs/heads/$branch.zip"
$zipPath   = "$env:TEMP\skills-for-teachers.zip"
$extPath   = "$env:TEMP\skills-for-teachers-extract"
$skillsDir = "$env:USERPROFILE\.claude\skills"

Write-Host ""
Write-Host "📚 learn-claude-code 설치 중..." -ForegroundColor Cyan
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

Write-Host "✅ 설치 완료!" -ForegroundColor Green
Write-Host ""
Write-Host "Claude Code를 재시작한 뒤 이렇게 말해보세요:" -ForegroundColor White
Write-Host '  "Claude Code 배우고 싶어"' -ForegroundColor Cyan
Write-Host '  "/learn-claude-code"' -ForegroundColor Cyan
Write-Host ""
