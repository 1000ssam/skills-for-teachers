# notion-to-docs 설치 스크립트 (Windows PowerShell)
# 사용법: PowerShell에서 아래 명령어 실행
#   irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/notion-to-docs/install.ps1 | iex

$ErrorActionPreference = "Stop"

$repo = "1000ssam/skills-for-teachers"
$branch = "main"
$skillName = "notion-to-docs"
$zipUrl = "https://github.com/$repo/archive/refs/heads/$branch.zip"
$tmpDir = Join-Path $env:TEMP "notion-to-docs-install"
$skillsDir = Join-Path $env:USERPROFILE ".claude\skills"

Write-Host ""
Write-Host "📂 notion-to-docs 설치 중..."
Write-Host ""

# 1. 임시 폴더 생성
if (Test-Path $tmpDir) { Remove-Item $tmpDir -Recurse -Force }
New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null

# 2. .claude/skills 폴더 생성
if (-not (Test-Path $skillsDir)) {
    New-Item -ItemType Directory -Path $skillsDir -Force | Out-Null
}

# 3. ZIP 다운로드
Write-Host "📥 다운로드 중..."
$zipPath = Join-Path $tmpDir "skills.zip"
try {
    Invoke-WebRequest -Uri $zipUrl -OutFile $zipPath -UseBasicParsing
} catch {
    Write-Host ""
    Write-Host "❌ 다운로드 실패. 인터넷 연결을 확인해 주세요."
    Remove-Item $tmpDir -Recurse -Force
    exit 1
}

# 4. 압축 해제
Expand-Archive -Path $zipPath -DestinationPath $tmpDir -Force

# 5. 스킬 복사 (기존 config.json, token.json 보존)
$src = Join-Path $tmpDir "skills-for-teachers-$branch\skills\$skillName"
$dst = Join-Path $skillsDir $skillName

if (Test-Path $dst) {
    $configBak = $null
    $tokenBak = $null
    $configPath = Join-Path $dst "config.json"
    $tokenPath = Join-Path $dst "token.json"
    if (Test-Path $configPath) { $configBak = Get-Content $configPath -Raw }
    if (Test-Path $tokenPath) { $tokenBak = Get-Content $tokenPath -Raw }
}

if (Test-Path $dst) { Remove-Item $dst -Recurse -Force }
Copy-Item $src $dst -Recurse

# 백업 복원
if ($configBak) { Set-Content (Join-Path $dst "config.json") $configBak }
if ($tokenBak) { Set-Content (Join-Path $dst "token.json") $tokenBak }

# 6. 임시 파일 정리
Remove-Item $tmpDir -Recurse -Force

Write-Host ""
Write-Host "✅ 설치 완료!"
Write-Host ""
Write-Host "다음 단계:"
Write-Host "  1. Notion Integration 토큰을 준비하세요"
Write-Host "     https://www.notion.so/profile/integrations → '새 API 통합' → 토큰 복사"
Write-Host "  2. Claude Code를 재시작한 뒤 이렇게 말해보세요:"
Write-Host '     "노션 문서 변환해줘"'
Write-Host "     (처음 실행 시 Notion 토큰 + Google 로그인을 안내합니다)"
Write-Host ""
Write-Host "⚠️  Node.js 18 이상이 필요합니다: https://nodejs.org"
Write-Host ""
