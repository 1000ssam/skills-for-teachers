---
name: ppt-lab-rebuild
description: 그리드 기반 클린룸 PPT 생성 하네스 (기존 ppt-lab의 1차원리 재창조판 — 별개 스킬). 공개 디자인 캐논(Müller-Brockmann 그리드 · Zelazny 차트)에서 도출한 12×8 모듈러 그리드 + 23 아키타입(7 family)으로 1920×1080 PPTX를 빌드한다. 레이아웃·스타일·팔레트 3축 직교 + 110 design-pick 룩(MIT) 통째 선택. 이미지 카드·미디어 슬롯·차트 20종 지원. Use when 사용자가 'ppt-lab-rebuild', '리빌드', '클린룸 ppt', '그리드 기반 덱', '재창조판 ppt-lab', '23 아키타입'을 명시할 때. (기존 ppt-lab=흡수 모델과 별개. 일반 'ppt 만들어줘'는 ppt-deck/ppt-lab 우선 — 이 스킬은 명시적 호출 시)
---

# ppt-lab — 그리드 기반 클린룸 PPT 하네스

외부 카탈로그를 상속하거나 레퍼런스를 측정하지 않는다. **공개 디자인 캐논에서 1차 원리로 도출한 자작 그리드**(`grid.json`)에서 모든 레이아웃 좌표를 결정론적으로 생성한다. 출처·자작 범위는 [`CANON.md`](CANON.md), 외부 라이선스 자산(룩·팔레트)은 [`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md).

## 직교 3축 + 룩 번들

```
레이아웃(layout) × 스타일(style) × 팔레트(palette)   + (옵션) 룩(look = style+palette 번들)
```
- **레이아웃** = 23 아키타입(7 family). **슬라이드마다** spec `variant`로 선택. 내용 보고 판단(허용).
- **스타일** = 폰트(latin/ea) + 카드(radius/border/shadow/accent). `--style`. (house·myeongmungo·consulting·velis)
  - 폰트 블록은 선택적 `display: {latin, ea}` 티어 지원 — 있으면 표지/페이지헤딩(display·h1·h2)만 이 페이스로, 본문·소제목은 `latin/ea`로 렌더(없으면 본문 폰트로 폴백 = 무회귀). 세리프 룩 12종이 표지=송명(Song Myung)으로 이 티어를 쓴다.
- **팔레트** = 색 역할 램프. `--palette`. (7종 — 유효 id: 1,2,3,4,5,6,8 / 7번은 없음)
- **룩(look)** = design-pick 110종, style+palette를 한 번에 채우는 자기완결 번들. `--look <slug>`. 레이아웃은 항상 직교.

> 원칙: 레이아웃은 LLM이 내용에서 추론 OK. **스타일·색은 내용에서 추론 금지**(슬롭) — 룩/사용자 지정에서만.

## 실행 워크플로 (필수 — 순서 준수, 건너뛰기 금지)

> 🚩 **룩·스타일·팔레트는 LLM이 임의로 고르지 않는다.** 아래 2단계(룩 선택 게이트)를 반드시 거친 뒤에만 빌드한다. 이 확인 없이 빌드하면 규칙 위반.

1. **콘텐츠 파악** — 자료·목적·톤 확인. 레이아웃(아키타입)은 슬라이드 내용에서 추론 OK.
2. **룩 선택 게이트 (STOP — 사용자 확인 필수)**
   - **🖼 비주얼 갤러리 자동 오픈 (먼저)** — 이름만으로 110 룩을 고르기 어려우므로, 추천 전에 **룩 갤러리 HTML을 새로고침 후 브라우저로 띄운다**(색·폰트·라이트/다크를 눈으로 보고 고르게). best-effort, 실패 시 경로만 안내:
     ```bash
     cd references && python3 tools/render-look-gallery.py        # 토큰에서 즉석 생성(항상 최신)
     # WSL→Windows: Start-Process가 UNC 경로를 처리(cmd start는 UNC CWD라 거부됨)
     powershell.exe -NoProfile -Command "Start-Process '$(wslpath -w look-gallery.html)'" 2>/dev/null \
       || echo "갤러리: references/look-gallery.html 를 브라우저로 직접 여세요"
     ```
     (비-WSL/헤드리스 환경이면 자동 오픈 생략하고 경로만 안내한다.)
     갤러리는 트랙(PPT/WEB)·톤(라이트/다크) 필터 + 이름·폰트 검색을 지원. (PPTX COM 렌더가 아닌 토큰 목업 — 색·폰트·톤 미리보기용. 픽셀 정확 X.)
   - 그 위에서 덱의 목적·톤에 맞는 **룩 2~3개를 근거와 함께 추천**한다(예: IR/투자 → `ppt-samsung-ir-restrained`·`ppt-goldman-ir-deck` / 강의·에디토리얼 → `ppt-editorial-magazine` / 컨설팅 → `ppt-bcg-exhibit-deck`·`ppt-bain-results-deck` / 다크 키노트 → `ppt-dark-tech`). 전체 목록·토큰은 [`design-tokens.json`](references/design-tokens.json)의 `looks`. (레이아웃 슬롯 와이어프레임은 별도 [`catalog.html`](references/catalog.html).)
   - 사용자가 **룩 슬러그를 직접 지정**하거나, 룩 대신 `--style`+`--palette` 조합을 고를 수도 있다 — 어느 쪽이든 **사용자 확인을 받는다.**
   - **다크 덱**을 원하면 다크 룩(`ppt-dark-tech`)을 고르거나, 아무 룩 + spec 최상위 `"canvas":"#0C1A17"`(어두운 hex)로 그 배경 색조의 다크 덱을 만들 수 있다(역할 팔레트 자동 도출). 상세: [`spec-schema.md`](references/spec-schema.md) §1.
   - 사용자가 **"아무거나/알아서 골라"라고 명시하기 전에는 빌드하지 않는다.**
3. **확정 후 빌드** — 선택된 `--look`(또는 `--style`+`--palette`)으로 `build-template.py` 실행.
4. **시각 QA → 보고** — `qa-runner.sh` 렌더 → PNG 직접 확인 → 사용자 보고.

> 자율 실행(/goal 등)에서도 룩은 **합리적 기본값을 1개 골라 "○○ 룩으로 진행합니다" 한 줄 고지**하고 즉시 되돌릴 여지를 준다(사소한 질문 금지 원칙과 양립). 룩은 덱의 디자인 정체성이라 묵시적으로 넘어가지 않는다.

## 23 아키타입 (7 family) — 권위: [`archetypes.md`](references/archetypes.md)

```
덱 뼈대?       → Frame    cover · section · agenda · closing
한 메시지?     → Focus    statement · feature
병렬 나열?     → Set      duo · trio · grid · list
명시적 비교?   → Contrast versus · matrix · rank
2축 배치?      → Field    quadrant · map
순서·구조?     → Structure flow · system
데이터?        → Data     share · bars · trend · spread · correlate · kpi
```
좌표는 전부 `grid.json`의 `grid_box(c0,cspan,r0,rspan)`에서 파생(매직넘버 없음). 분류 도출 근거는 archetypes.md.

## 이미지·미디어 슬롯 (수업·자료용 핵심)

이미지는 아키타입이 아니라 **슬롯 fill 종류**. `feature`의 큰 미디어, `duo`/`trio`/`grid` 카드별 `image`(이미지 카드 = 사진+설명 2컬럼).
- spec `image: {src:"경로", fit:"cover|contain", caption:"…"}` → 실제 이미지 삽입(cover 크롭/contain 레터박스).
- `src` 없거나 `{}` → **플레이스홀더 박스**("이미지 자리" + 권장 비율 + 도형 픽토, 이모지 없음). 자리만 잡고 나중에 교체.
- 경로는 절대경로 또는 spec 파일 기준 상대경로(WSL이면 `/mnt/c/...` 마운트 경로).

## 차트 20종 — `chart()` 헬퍼

- **네이티브(python-pptx)**: column(clustered/stacked/stacked_100) · bar · line · line_markers · area · pie · doughnut · radar · xy_scatter · bubble
- **합성(도형)**: waterfall · funnel · gauge · gantt · tam_sam_som · bullet · slope · kpi_cards
- Data 아키타입 spec에서 `chart.type`으로 선택. 활성 팔레트 색 적용.
- `kpi` 카드 배열 키: **`items`(권장)** · `kpis` · `stats` (셋 다 허용, Set·List와 키 일관). 항목 `{value, label, note?}`.

## 빌드 / QA

```bash
cd references
# 그리드 → layouts.json 재생성 (좌표 SSOT 변경 시)
python3 tools/gen-layouts.py
# 빌드 (스타일/팔레트 또는 룩 선택)
python3 tools/build-template.py /tmp/out.pptx --spec demo/all-archetypes.spec.json --style house --palette 1
python3 tools/build-template.py /tmp/out.pptx --spec spec.json --look ppt-samsung-ir-restrained   # 룩 통째
# 시각 QA (Windows PowerPoint COM 렌더 → PNG)
bash tools/qa-runner.sh /tmp/out.pptx     # → /tmp/out_qa/images/slide_N.png
```
spec: `{ "style":"house", "palette":1, "slides":[ {"archetype":"duo","data":{...}} ] }` (`variant`는 `archetype`의 alias). **`data` 입력 키 권위는 [`spec-schema.md`](references/spec-schema.md)** — 아키타입별 필수/선택/alias·최소 예시.

## 파일 맵 (SSOT)

- `references/grid.json` — 그리드 SSOT(12×8 모듈러, 좌표 파생식)
- `references/archetypes.md` — 23 아키타입 분류·슬롯·도출 근거
- `references/spec-schema.md` — 아키타입별 spec `data` 입력 키(필수/선택/alias·최소 예시). `build_*` 함수 추출 권위본
- `references/layouts.json` — gen-layouts.py 생성물(좌표). **직접 수정 금지** → grid.json/gen-layouts.py 수정 후 재생성
- `references/design-tokens.json` — palettes(7) · styles(4) · looks(110)
- `references/tools/` — build-template.py(엔진) · gen-layouts.py · render-catalog.py · qa-runner.sh · extract-*.py(중립 측정도구)
- `CANON.md` · `THIRD-PARTY-NOTICES.md` — 출처/라이선스

## 환경 메모

- 빌드: WSL python3 + python-pptx. 렌더 QA: Windows PowerPoint COM(soffice 아님).
- 폰트 미설치 시 PowerPoint 대체. 한글은 Pretendard 폴백.
- 산출물 경로는 자유(`/tmp/` 등). WSL→Windows 공유 폴더는 `/mnt/c/...`.
