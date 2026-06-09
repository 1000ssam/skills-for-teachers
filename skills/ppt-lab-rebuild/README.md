# 🎨 ppt-lab-rebuild (그리드 기반 PPT 생성 하네스)

수업 자료·발표 덱을 **디자인 그리드에서 결정론적으로** 만들어 주는 Claude Code 스킬입니다. 슬라이드 내용을 주면 1920×1080 PPTX를 빌드합니다 — 색·폰트·레이아웃은 검증된 디자인 토큰에서 나오므로 "AI가 만든 듯한" 뻔한 결과로 수렴하지 않습니다.

레이아웃은 공개 디자인 캐논(Müller-Brockmann 그리드 · Zelazny 차트 분류)에서 **1차 원리로 도출한 자작 그리드**를 쓰고, 색·폰트·카드 스타일은 [Design Diversity](https://github.com/epoko77-ai/design-diversity)(MIT)의 110개 디자인 룩을 토큰으로 흡수했습니다.

---

## 무엇이 다른가

- **직교 3축** — 레이아웃(23 아키타입) × 스타일(폰트·카드) × 팔레트(색)를 독립적으로 조합.
- **110개 디자인 룩** — IR·컨설팅·에디토리얼·다크 키노트 등 완성된 스타일+팔레트 번들을 통째로 선택.
- **클린룸** — 외부 PPTX를 복제·측정하지 않고 그리드 좌표를 코드로 생성(매직넘버 없음).
- **차트 20종 · 이미지 카드 · 다크 모드** — 배경색 하나만 주면 팔레트를 자동 도출.
- **Human-in-the-loop** — 룩·스타일은 임의로 고르지 않고 갤러리를 띄워 사용자 확인 후 빌드.

## 설치

PowerShell에서 실행:

```powershell
irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/ppt-lab-rebuild/install.ps1 | iex
```

macOS / Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/ppt-lab-rebuild/install.sh | bash
```

### 필요 환경

- [Claude Code](https://claude.ai/claude-code)
- Python 3.10+
- Python 패키지: `python-pptx`, `pillow` (설치 스크립트가 자동 설치)
- **렌더 QA(미리보기 이미지)** 는 다음 중 하나가 필요합니다:
  - Windows + PowerPoint (COM 렌더, 가장 정확) — WSL에서도 호출 가능
  - 또는 LibreOffice (`soffice`) — PDF→이미지 폴백
  - 둘 다 없으면 PPTX 빌드는 되지만 미리보기 이미지는 생성되지 않습니다.

## 사용법

Claude Code에서 명시적으로 호출합니다(일반 "PPT 만들어줘"와 구분):

```
ppt-lab-rebuild 로 강의 자료 만들어줘
그리드 기반 덱으로 IR 자료 만들어줘
```

진행 흐름:

1. **내용 파악** — 자료·목적·톤을 확인하고 슬라이드별 레이아웃(아키타입)을 정합니다.
2. **룩 선택 게이트(확인 필수)** — `look-gallery.html`(색·폰트·라이트/다크 미리보기)을 띄우고 목적에 맞는 룩 2~3개를 근거와 함께 추천합니다. 슬러그를 직접 지정하거나 `--style`+`--palette` 조합도 가능합니다.
3. **빌드** — 확정된 룩으로 PPTX를 생성합니다.
4. **시각 QA → 보고** — 렌더 이미지를 직접 확인한 뒤 보고합니다.

### 직접 빌드(수동)

```bash
cd skills/ppt-lab-rebuild/references
# 룩 통째로 선택
python3 tools/build-template.py out.pptx --spec spec.json --look ppt-editorial-magazine
# 또는 스타일+팔레트 조합
python3 tools/build-template.py out.pptx --spec demo/all-archetypes.spec.json --style house --palette 1
# 미리보기 렌더(Windows PowerPoint)
bash tools/qa-runner.sh out.pptx        # → out_qa/images/slide_N.png
```

`spec.json`의 입력 키(아키타입별 필수/선택)는 [`references/spec-schema.md`](references/spec-schema.md)가 권위 문서입니다.

## 디자인 룩 갤러리

```bash
cd references && python3 tools/render-look-gallery.py   # look-gallery.html 생성(항상 최신)
```

110개 룩을 미니 슬라이드 목업으로 보여 주며 트랙(PPT/WEB)·톤(라이트/다크) 필터와 이름·폰트 검색을 지원합니다. (토큰 미리보기 — 픽셀 정확한 PPTX 렌더는 아닙니다.)

## 폰트

이 하네스는 **폰트 이름(토큰)만** 배포하고 폰트 파일은 포함하지 않습니다. 룩이 사용하는 전체 폰트의 출처·라이선스·다운로드 링크는 한 페이지에 정리되어 있습니다:

```bash
cd references && python3 tools/render-font-links.py     # fonts.html 생성
```

→ [`references/fonts.html`](references/fonts.html) 를 브라우저로 엽니다. 대부분 Google Fonts(SIL OFL)이며, 한글은 Pretendard·MaruBuri·송명(Song Myung), 독점 폰트 4종은 재배포하지 않습니다.

**폴백 보장**: 한글 폰트가 없으면 Pretendard, 라틴 독점 폰트가 없으면 Inter로 자동 대체되어 빌드는 항상 성공합니다(글자 깨짐 없음). 한글 헤드라인 줄바꿈 품질을 높이려면 `PPT_LAB_FONT_DIR` 환경변수로 폰트 폴더를 지정할 수 있습니다(선택).

## 디렉토리 구조

```
ppt-lab-rebuild/
├── SKILL.md                     # Claude Code 스킬 정의
├── CANON.md                     # 방법론 출처(그리드·차트 캐논)
├── THIRD-PARTY-NOTICES.md       # 외부 자산 라이선스(룩·폰트)
└── references/
    ├── grid.json                # 12×8 모듈러 그리드 SSOT
    ├── archetypes.md            # 23 아키타입(7 family) 분류·슬롯
    ├── spec-schema.md           # 아키타입별 spec 입력 키 권위 문서
    ├── design-tokens.json       # 팔레트 7 · 스타일 4 · 룩 110
    ├── layouts.json             # 그리드 파생 좌표(생성물 — 직접 수정 금지)
    ├── look-gallery.html        # 룩 미리보기 갤러리(생성물)
    ├── fonts.html               # 폰트 출처·링크(생성물)
    └── tools/
        ├── build-template.py    # 엔진(PPTX 빌드)
        ├── gen-layouts.py       # grid.json → layouts.json
        ├── render-look-gallery.py
        ├── render-font-links.py
        └── qa-runner.sh         # PowerPoint COM 렌더
```

## 라이선스 & 크레딧

- **이 하네스의 자작물**(그리드 엔진·23 아키타입·코드·문서) — **MIT** (리포 루트 [`LICENSE`](../../LICENSE)).
- **방법론 출처** — Josef Müller-Brockmann *Grid Systems*, Gene Zelazny *Say It With Charts* 등. 아이디어 크레딧이며 표현은 복제하지 않았습니다. 상세: [`CANON.md`](CANON.md).
- **디자인 룩 110종** — [Design Diversity](https://github.com/epoko77-ai/design-diversity) (MIT)의 명세·토큰을 흡수. 각 룩 항목에 출처가 기록되어 있습니다.
- **velis 스타일/팔레트** — lrk-slides-velis (CC0 1.0).
- **폰트** — 각 배포처 라이선스(대부분 SIL OFL). 독점 폰트는 미포함·오픈 폴백.

전체 고지는 [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md)를 참조하세요.

> 산출물을 게시할 때는 본인의 회사명·로고·이미지를 사용하고, 라이선스가 없는 독점 폰트를 임베드하지 마세요. 룩 식별자에 등장하는 브랜드명은 그 스타일을 *묘사*하는 명목적 참조이며 해당 브랜드의 보증을 의미하지 않습니다.
