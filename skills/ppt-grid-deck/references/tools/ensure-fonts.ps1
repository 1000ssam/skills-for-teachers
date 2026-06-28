<#
  ensure-fonts.ps1 — 폰트 자동 프로비저닝 (없으면 받아서 설치)

  ppt-lab-rebuild 는 폰트 *이름*(토큰)만 배포하고 폰트 파일은 품지 않는다. 이 스크립트는
  렌더 전에 필요한 폰트가 이 PC 에 있는지 보장한다. 폰트마다 3단계:

    1) GDI 에 이미 설치됨            → 건너뜀
    2) 로컬 캐시(C:\dev\ppt-fonts)에 있음 → 캐시에서 설치
    3) 둘 다 없음                    → 출처에서 다운로드 → 캐시 저장 → 설치
         · Google Fonts 계열 : google-webfonts-helper(gwfh) API 로 직접 ttf URL 해소
         · Pretendard        : GitHub 릴리스 zip 에서 해당 weight ttf 추출
         · 그 외(MaruBuri·Clash): 자동 미지원 → 출처 링크 안내(수동 설치)

  설치는 per-user(관리자 불필요): %LOCALAPPDATA%\Microsoft\Windows\Fonts 복사 +
  HKCU Fonts 레지스트리 + AddFontResource + WM_FONTCHANGE 브로드캐스트
  (사용자 폰트가 PowerPoint COM 에 안 보이던 함정 회피 — 본진 install-fonts.ps1 과 동일 기법).

  사용:
    powershell -ExecutionPolicy Bypass -File ensure-fonts.ps1 -Faces "Pretendard Black","Archivo Black"
    powershell ... -File ensure-fonts.ps1 -Look ppt-neo-brutalism      # 그 룩이 쓰는 폰트만
    powershell ... -File ensure-fonts.ps1 -All                         # design-tokens.json 의 전 폰트
    ... -WhatIf      # 받지/설치하지 않고 무엇을 할지만 출력
#>
[CmdletBinding()]
param(
  [string[]]$Faces,
  [string]$Look,
  [switch]$All,
  [switch]$WhatIf
)
$ErrorActionPreference = 'Stop'
$HERE   = Split-Path -Parent $MyInvocation.MyCommand.Path
$TOKENS = Join-Path $HERE '..\design-tokens.json'
$CACHE  = 'C:\dev\ppt-fonts'
$USERFONTS = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$REG    = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'

Add-Type -AssemblyName System.Drawing
Add-Type -Name G -Namespace W -MemberDefinition '[DllImport("gdi32.dll")] public static extern int AddFontResource(string p);'
Add-Type -Name U -Namespace W -MemberDefinition '[DllImport("user32.dll")] public static extern int SendMessage(int h, uint m, int w, int l);'

# 한글이라 gwfh subset=korean 으로 받아야 하는 Google Fonts 패밀리
$KOREAN_GF = @('Song Myung','Gowun Batang','Noto Sans KR','Noto Serif KR')
# Google Fonts 가 아닌(=gwfh 로 못 받는) 폰트의 출처 명세
$NONGOOGLE = @{
  'Pretendard'       = @{ type='pretendard'; weight='Regular' }
  'Pretendard Black' = @{ type='pretendard'; weight='Black'   }
  'MaruBuri'         = @{ type='manual'; url='https://hangeul.naver.com/maruburi' }
  'Clash Display'    = @{ type='manual'; url='https://www.fontshare.com/fonts/clash-display' }
  'Arial'            = @{ type='system' }   # OS 기본
}
# 미설치 시 오픈 폴백으로 처리(받을 필요 없음) — 빌더가 Inter/Pretendard 로 대체
$FALLBACK_OK = @('Futura','Helvetica Neue','SF Pro Display','Hyundai Sans Head')

function Test-Installed([string]$face) {
  $ifc = New-Object System.Drawing.Text.InstalledFontCollection
  return [bool]($ifc.Families | Where-Object { $_.Name -eq $face })
}

function Find-InCache([string]$face) {
  # 캐시 폴더(공백→밑줄 / 첫 단어)에서 weight 매칭 ttf 를 찾는다
  $weightWords = 'black','heavy','extrabold','semibold','bold','medium','light','thin','regular'
  $named = ($weightWords | Where-Object { $face.ToLower().Contains($_) } | Select-Object -First 1)
  foreach ($folder in @(($face -replace ' ','_'), ($face -split ' ')[0])) {
    $d = Join-Path $CACHE $folder
    if (Test-Path $d) {
      $ttfs = Get-ChildItem $d -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -in '.ttf','.otf' }
      $hit = $null
      if ($named) { $hit = $ttfs | Where-Object { $_.Name.ToLower().Contains($named) } | Select-Object -First 1 }
      if (-not $hit) { $hit = $ttfs | Where-Object { $_.Name.ToLower().Contains('regular') } | Select-Object -First 1 }
      if (-not $hit) { $hit = $ttfs | Select-Object -First 1 }
      if ($hit) { return $hit.FullName }
    }
  }
  return $null
}

function Install-TTF([string]$path, [string]$face) {
  if ($WhatIf) { Write-Host "  [WhatIf] install $([IO.Path]::GetFileName($path))"; return }
  New-Item -ItemType Directory -Force -Path $USERFONTS | Out-Null
  $dst = Join-Path $USERFONTS ([IO.Path]::GetFileName($path))
  try { Copy-Item $path -Destination $dst -Force -ErrorAction Stop }
  catch { Write-Host "  이미 설치된 파일 사용 중(건너뜀)" -ForegroundColor DarkGray; return }
  $kind = if ([IO.Path]::GetExtension($path) -ieq '.otf') { 'OpenType' } else { 'TrueType' }
  $regName = "{0} ({1})" -f ([IO.Path]::GetFileNameWithoutExtension($path)), $kind
  New-ItemProperty -Path $REG -Name $regName -Value $dst -PropertyType String -Force | Out-Null
  [void][W.G]::AddFontResource($dst)
  [void][W.U]::SendMessage(0xffff, 0x1D, 0, 0)   # WM_FONTCHANGE 브로드캐스트
  Write-Host "  installed -> $dst" -ForegroundColor Green
}

function Save-ToCache([string]$face, [string]$srcTtf) {
  # 받은 ttf 를 캐시 폴더에 보존(다음 PC/다음 실행 재사용)
  $folder = Join-Path $CACHE ($face -replace ' ','_')
  New-Item -ItemType Directory -Force -Path $folder | Out-Null
  $dst = Join-Path $folder ([IO.Path]::GetFileName($srcTtf))
  Copy-Item $srcTtf -Destination $dst -Force
  return $dst
}

function Resolve-GoogleTTF([string]$face) {
  # gwfh API → 직접 ttf URL (gstatic). id = 소문자-하이픈, 한글은 subset=korean.
  $id = ($face.ToLower() -replace ' ','-')
  $subset = if ($KOREAN_GF -contains $face) { 'korean' } else { 'latin' }
  $api = "https://gwfh.mranftl.com/api/fonts/$id`?subsets=$subset"
  try { $meta = Invoke-RestMethod -Uri $api -TimeoutSec 25 } catch { return $null }
  if (-not $meta.variants) { return $null }
  $v = ($meta.variants | Where-Object { $_.id -eq $meta.defVariant }) | Select-Object -First 1
  if (-not $v) { $v = $meta.variants | Select-Object -First 1 }
  return $v.ttf
}

$script:PretendardZip = $null
function Get-PretendardTTF([string]$weight) {
  # 릴리스 zip(최신)을 1회 받아 펼친 뒤 Pretendard-<weight> 폰트를 찾는다.
  # 우선순위: public/static/Pretendard-<w>.otf (기본 디자인) → 그 외 위치의 .ttf(대체 글꼴).
  if (-not $script:PretendardZip) {
    $rel = Invoke-RestMethod "https://api.github.com/repos/orioncactus/pretendard/releases/latest" -TimeoutSec 25
    $asset = $rel.assets | Where-Object { $_.name -match '^Pretendard-[\d.]+\.zip$' } | Select-Object -First 1
    if (-not $asset) { return $null }
    $tmp = Join-Path $env:TEMP ("pretendard_" + $rel.tag_name)
    $zip = "$tmp.zip"
    if (-not (Test-Path $tmp)) {
      Write-Host "  downloading $($asset.name) ($([int]($asset.size/1MB))MB)..." -ForegroundColor DarkGray
      Invoke-WebRequest $asset.browser_download_url -OutFile $zip -TimeoutSec 300
      Expand-Archive $zip -DestinationPath $tmp -Force
    }
    $script:PretendardZip = $tmp
  }
  $all = Get-ChildItem $script:PretendardZip -Recurse -ErrorAction SilentlyContinue |
         Where-Object { $_.Name -ieq "Pretendard-$weight.otf" -or $_.Name -ieq "Pretendard-$weight.ttf" }
  $pick = $all | Where-Object { $_.FullName -notmatch 'alternative' -and $_.Extension -ieq '.otf' } | Select-Object -First 1
  if (-not $pick) { $pick = $all | Where-Object { $_.Extension -ieq '.otf' } | Select-Object -First 1 }
  if (-not $pick) { $pick = $all | Select-Object -First 1 }
  return $pick.FullName
}

function Ensure-Face([string]$face) {
  if (-not $face) { return }
  Write-Host "• $face"
  if ($FALLBACK_OK -contains $face) { Write-Host "  독점 → 오픈 폴백(받지 않음)" -ForegroundColor DarkGray; return }
  if (Test-Installed $face)         { Write-Host "  이미 설치됨 ✓" -ForegroundColor DarkGray; return }

  # 2) 로컬 캐시
  $cached = Find-InCache $face
  if ($cached) { Write-Host "  캐시에서 설치: $([IO.Path]::GetFileName($cached))"; Install-TTF $cached $face; return }

  # 3) 다운로드
  $ng = $NONGOOGLE[$face]
  if ($ng -and $ng.type -eq 'system') { Write-Host "  시스템 기본(설치 불필요)" -ForegroundColor DarkGray; return }
  if ($ng -and $ng.type -eq 'manual') { Write-Warning "  자동 미지원 → 수동 설치: $($ng.url)"; return }

  $ttf = $null
  if ($ng -and $ng.type -eq 'pretendard') {
    if ($WhatIf) { Write-Host "  [WhatIf] Pretendard 릴리스 zip → $($ng.weight)"; return }
    $ttf = Get-PretendardTTF $ng.weight
  } else {
    $url = Resolve-GoogleTTF $face
    if ($url) {
      if ($WhatIf) { Write-Host "  [WhatIf] gwfh → $url"; return }
      $ttf = Join-Path $env:TEMP ([IO.Path]::GetFileName(($url -split '\?')[0]))
      if ($ttf -notmatch '\.ttf$') { $ttf = "$ttf.ttf" }
      Invoke-WebRequest $url -OutFile $ttf -TimeoutSec 120
    }
  }
  if (-not $ttf -or -not (Test-Path $ttf)) { Write-Warning "  해소 실패 — 직접 설치 필요(fonts.html 참조)"; return }
  $kept = Save-ToCache $face $ttf
  Install-TTF $kept $face
}

# ── 대상 폰트 목록 결정 ──
function Faces-From-Tokens([string]$onlyLook) {
  # UTF-8 명시 — PowerShell 5.x 가 UTF-8 JSON 을 CP949 로 오독해 한글이 깨지는 것 방지
  $t = Get-Content $TOKENS -Raw -Encoding UTF8 | ConvertFrom-Json
  $set = New-Object System.Collections.Generic.HashSet[string]
  $looks = $t.looks.PSObject.Properties
  foreach ($p in $looks) {
    if ($onlyLook -and $p.Name -ne $onlyLook) { continue }
    $f = $p.Value.fonts
    if (-not $f) { continue }
    foreach ($n in @($f.latin, $f.ea, $f.display.latin, $f.display.ea)) { if ($n) { [void]$set.Add($n) } }
  }
  return $set
}

$targets = if ($Faces) { $Faces }
           elseif ($Look) { Faces-From-Tokens $Look }
           elseif ($All)  { Faces-From-Tokens $null }
           else { Write-Host "대상 미지정 — -Faces / -Look <slug> / -All 중 하나"; exit 1 }

Write-Host "=== ensure-fonts: $((@($targets)).Count)종 점검 ===" -ForegroundColor Cyan
foreach ($f in $targets) {
  # per-font 가드 — 한 폰트 다운로드/설치 실패가 나머지를 멈추지 않게
  try { Ensure-Face $f } catch { Write-Warning "  $f 처리 실패: $($_.Exception.Message)" }
}
Write-Host "=== 완료 ===" -ForegroundColor Cyan
