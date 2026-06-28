# spec-schema.md — 아키타입별 입력 스키마 레퍼런스

`build-template.py`의 각 `build_*` 함수가 **실제로 읽는 키**를 코드에서 추출해 확정한 문서다.
`archetypes.md`는 아키타입의 *과업·레이아웃 슬롯·도출 근거*를 설명하고, 이 문서는 *spec.json의 `data`에 어떤 키를 넣어야 하는지*를 다룬다.

> 권위: `references/tools/build-template.py` (이 문서는 그 파생물). 코드가 바뀌면 이 문서도 갱신한다.
> 검수용 최소 spec: `references/demo/schema-smoke.spec.json` (23 아키타입 1장씩 최소 입력).

---

## 1. spec 최상위 구조

```json
{
  "title": "덱 제목",
  "style": "house",
  "palette": 1,
  "look": "ppt-samsung-ir-restrained",
  "slides": [
    { "archetype": "cover", "data": { } }
  ]
}
```

| 키 | 타입 | 설명 |
|---|---|---|
| `title` | string | 덱 제목(메타용, 렌더에는 직접 안 쓰임) |
| `style` | string | 스타일 프리셋(house·myeongmungo·consulting·velis). **선택** |
| `palette` | int | 팔레트 id(유효: 1,2,3,4,5,6,8 — 7번 없음). **선택** |
| `look` | string | design-pick 룩 슬러그(style+palette 번들). **선택** |
| `size` | string | 글자 크기 티어 `소`/`중`/`대`(s/m/l). 룩과 직교 — 본문 위주로 키움(소=룩 본연·중≈22.5pt·대≈25pt). CLI `--size` 우선. **선택** |
| `canvas` | string(#hex) | **덱 배경색**. 어두운 값이면 다크 모드 자동 진입 — 잉크/서피스/디바이더 역할 팔레트가 이 색조에 맞춰 자동 도출된다(라이트 룩에도 적용 가능). **선택** |
| `dark` | bool | 다크 모드 강제 on/off(휘도 자동감지 오버라이드). 보통 불필요 — `canvas`만으로 자동 판정. **선택** |
| `slides[]` | array | 슬라이드 배열 |

### 다크 캔버스 (배경색 → 팔레트 자동 도출)
- 룩이 `palette.canvas`(또는 spec 최상위 `canvas`)에 **어두운 #hex**를 선언하면 그 덱은 다크로 렌더된다.
- 엔진이 캔버스 휘도로 다크를 자동 감지(`is_dark`, WCAG 상대휘도 < 0.30)하고, **canvas 색조로부터** `ink/ink-2/body/muted/subtle/surface/surface-2/surface-3/divider/hairline/slab/on-ink/on-accent` 역할 토큰을 **결정론적으로 도출**(`derive_dark_roles`)한다 → 서피스가 항상 배경 색조와 조화.
- 라이트 모드에선 역할 토큰이 기존 `navy/slate-*/white` 별칭이라 **무회귀**(바이트 동일). 빌더는 raw 색 대신 역할 토큰을 읽는다.
- 룩이 특정 역할을 직접 정의하면 그 값을 존중(도출이 덮지 않음). 예: `ppt-dark-tech`는 `canvas` 하나만 선언 → 나머지 전부 자동 도출.
- 예: `"canvas": "#14102E"` (딥 인디고) → 인디고 색조 다크 덱. `"canvas": "#0C1A17"` (딥 틸) → 틸 다크 덱.

**최상위 `style`/`palette`/`look`/`canvas`/`dark`는 빌더가 읽는다**(`spec.get("style")` 등). 단 **CLI 옵션이 우선**한다:
- `--style`/`--palette`가 주어지면 spec의 값을 덮어쓴다.
- `--look`이 주어지면 그 룩의 style+palette를 통째 적용하고, 명시 `--style`/`--palette`만 부분 오버라이드한다.
- 즉 spec에 색·스타일을 박아도 CLI에서 바꿀 수 있다. 룩과 개별 style/palette를 동시에 주면 룩이 베이스, 개별 옵션이 덮어쓰기.

### slides[] 항목

```json
{ "archetype": "duo", "data": { } }
```

| 키 | 타입 | 설명 |
|---|---|---|
| `archetype` | string | 아키타입 슬러그(23종). **alias: `variant`** |
| `data` | object | 아키타입별 입력(아래 §3~§6) |

> 라우팅: `sl.get("archetype") or sl.get("variant", "statement")`. 알 수 없는 슬러그 → `statement`로 폴백 + 경고.

---

## 2. 공통 규칙

- 각 슬라이드는 `{ "archetype": "...", "data": {...} }` 구조.
- **헤더 공통 키** — Focus·Set·Contrast·Field·Structure·Data 패밀리(=`header()`를 쓰는 17종)는 모두 받는다:
  - `kicker` (상단 작은 라벨). **alias: `eyebrow`**
  - `title` (슬라이드 제목)
  - Frame 패밀리(cover·section·agenda·closing)는 `header()`를 안 쓰고 **자체 슬롯**을 쓴다(키는 §3 참조).
- **배열형 콘텐츠의 기본 키는 `items`**. 단 일부 아키타입은 빌더 내부 모델 때문에 다른 키를 쓴다(아래 표·§7 alias 정책):
  - matrix·rank → `rows`, flow → `steps`, system → `nodes`, versus → `left`/`right`,
    quadrant → `cells`, map·correlate → `points`, Data 차트 → `categories`/`series`/`values`.
- **이미지·미디어 입력**은 `{ "src": "...", "fit": "cover|contain", "caption": "..." }`(§ 미디어).
- `footer()` 헬퍼(caption·pageno)는 정의돼 있으나 **현재 어떤 빌더도 호출하지 않는다**(향후용).

---

## 3. Frame 패밀리 (자체 슬롯, `header()` 미사용)

### cover
```json
{ "archetype": "cover", "data": {
  "kicker": "WORLD HISTORY", "bg": "navy",
  "title": "덱 제목", "subtitle": "부제", "meta": "날짜 · 작성자"
} }
```
| 키 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `title` | string | 권장 | 디스플레이 제목. `\n` 줄바꿈 허용 |
| `bg` | string(색토큰) | 선택 | 배경색(기본 `white`). `white`/`slate-50`/`blue-faint` 외 → 다크모드(글자 흰색) |
| `kicker` | string | 선택 | 상단 라벨. **alias: `eyebrow`** |
| `subtitle` | string | 선택 | 부제 |
| `meta` | string | 선택 | 하단 메타(날짜·작성자 등) |
| `background` | media obj | 선택 | 풀블리드 배경 이미지(`fit=cover` 고정) |

### section
```json
{ "archetype": "section", "data": {
  "index": "01", "bg": "navy", "title": "섹션 제목", "caption": "섹션 설명"
} }
```
| 키 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `title` | string | 권장 | 섹션 제목. **alias: `section_title`** |
| `bg` | string | 선택 | 배경색(기본 `navy`) |
| `index` | string/number | 선택 | 큰 인덱스("01" 등) |
| `caption` | string | 선택 | 보조 설명 |
| `background` | media obj | 선택 | 풀블리드 배경 이미지 |

### agenda
```json
{ "archetype": "agenda", "data": {
  "kicker": "AGENDA", "title": "목차",
  "items": ["항목 1", { "title": "항목 2", "note": "보조 설명" }]
} }
```
| 키 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `items[]` | array | 필수 | `string` 또는 `{ "title": "...", "note": "..." }`. 번호는 자동(01,02…) |
| `title` | string | 선택 | 제목(기본 "목차") |
| `kicker` | string | 선택 | 기본 "AGENDA". **alias: `eyebrow`** |

### closing
```json
{ "archetype": "closing", "data": {
  "kicker": "NEXT", "bg": "navy", "title": "마무리 메시지",
  "subtitle": "부제", "cta": "데모 빌드 →"
} }
```
| 키 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `title` | string | 권장 | 제목 |
| `bg` | string | 선택 | 배경색(기본 `navy`) |
| `kicker` | string | 선택 | **alias: `eyebrow`** |
| `subtitle` | string | 선택 | 부제 |
| `cta` | string | 선택 | 파란 버튼 라벨 |

---

## 4. Focus 패밀리 (`header()` 사용 → `kicker`/`title` 공통)

### statement
```json
{ "archetype": "statement", "data": {
  "kicker": "핵심 주장", "title": "슬라이드 제목",
  "lead": "핵심 문장", "support": ["근거 1", "근거 2"]
} }
```
| 키 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `lead` | string | 권장 | 큰 핵심 문장(h2) |
| `support` | string \| string[] | 선택 | 배열이면 불릿, 문자열이면 단락 |
| `image` | media obj | 선택 | 있으면 우측 미디어 + 근거는 좌측만 차지 |
| `kicker`/`title` | string | 선택 | 헤더 공통 |

### feature
```json
{ "archetype": "feature", "data": {
  "kicker": "사례", "title": "히어로 + 인사이트",
  "bullets": ["요점 1", "요점 2"],
  "media": { "src": "image.png", "fit": "contain", "caption": "이미지 설명" }
} }
```
| 키 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `bullets` | string[] | 택1 | 좌측 본문 불릿 |
| `body` | string | 택1 | `bullets` 없을 때 단락 본문(둘 다 없으면 빈 본문). **`body` 허용됨**(코드 확인) |
| `media` | media obj | 선택 | 우측 큰 미디어. 없으면 플레이스홀더 |
| `kicker`/`title` | string | 선택 | 헤더 공통 |

### showcase
```json
{ "archetype": "showcase", "data": {
  "kicker": "공식 1", "title": "차트 유형은 꺾은선그래프로",
  "bullets": ["증가·감소·급변 한눈에", "곡선 토글로 선 모양 조정"],
  "media": { "src": "screenshot.png", "caption": "선택 캡션" }
} }
```
| 키 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `media` | media obj | 권장 | **헤더와 같은 좌측 마진에 정렬·무크롭·무왜곡**(비율 보존 rect 계산) + **활성 룩의 카드 스킨(border/shadow) 자동 상속**(brutalism=검정+하드섀도 / dark-luxury=골드 헤어라인 / swiss 등 플랫=맨몸). `image` 도 alias. 없으면 플레이스홀더. `fit`는 무시(항상 비율 보존) |
| `bullets` | string[] | 선택 | 본문 불릿. **배치는 이미지 종횡비로 자동** — 영역(넓고 낮음)보다 세로로 길면(대부분 스크린샷, ar≲2.9) 이미지 좌측·전체높이 + **불릿 우측**, 가로로 길면(울트라와이드) 이미지 상단 + **불릿 하단**. 사용자 결정 불필요 |
| `kicker`/`title` | string | 선택 | 헤더 공통(좌측정렬) |

> `feature`(우측 반쪽·cover 크롭) vs `showcase`(좌측정렬·무크롭+불릿 자동배치) — 미디어가 곧 메시지(가이드·UI 캡처·도표)면 showcase. 와이드 스크린샷은 showcase가 정답(cover로 자르면 디테일 손실).

---

## 5. Set 패밀리 (`header()` 사용 · 카드 모델 공유)

카드 항목(item)은 `_content_card()`가 처리한다. 항목 공통 형태:

| 항목 키 | 타입 | 설명 |
|---|---|---|
| `label` | string | 카드 상단 라벨(accent색, 대문자) |
| `heading` | string | 카드 제목(h3) |
| `bullets` | string[] | 본문 불릿(있으면 `body`보다 우선) |
| `body` | string | 본문 단락 |
| `image` | media obj | **키 존재 시** 이미지 카드(상단 55% 밴드). `{}`(빈 dict)면 플레이스홀더 |

### duo
```json
{ "archetype": "duo", "data": {
  "kicker": "비교 아님", "title": "두 항목",
  "items": [
    { "label": "A", "heading": "항목 A", "bullets": ["요점 1", "요점 2"] },
    { "label": "B", "heading": "항목 B", "body": "설명", "image": { "src": "img.png", "fit": "cover" } }
  ]
} }
```
- `items[]` (2개). **fallback: `left`/`right`** — `items` 없으면 `[left, right]`로 구성.

### trio
```json
{ "archetype": "trio", "data": { "title": "세 항목", "items": [ {…}, {…}, {…} ] } }
```
- `items[]` (최대 3). **fallback: `columns`**.

### grid
```json
{ "archetype": "grid", "data": { "title": "4업", "items": [ {…}, {…}, {…}, {…} ] } }
```
- `items[]` (최대 6). **fallback: `cells`**. 개수에 따라 2~3열 자동(n>4 → 3열, n>2 → 2행).

### list
```json
{ "archetype": "list", "data": {
  "kicker": "단계", "title": "순서",
  "items": [ { "title": "1단계", "body": "설명" }, "단순 문자열도 가능" ]
} }
```
| 항목 키 | 타입 | 설명 |
|---|---|---|
| `items[]` | array | `string` 또는 `{ "title": "...", "body": "..." }`. 번호 오토(1,2,3…) |

---

## 6. Contrast 패밀리 (`header()` 사용)

### versus
```json
{ "archetype": "versus", "data": {
  "kicker": "대비", "title": "A vs B",
  "left":  { "label": "BEFORE", "heading": "왼쪽 주장", "points": ["근거 1", "근거 2"] },
  "right": { "label": "AFTER",  "heading": "오른쪽 주장", "points": ["근거 1", "근거 2"] }
} }
```
| 키 | 타입 | 설명 |
|---|---|---|
| `left` / `right` | object | `{ label, heading, points[] }`. `label` 기본값 BEFORE/AFTER |
| `*.points[]` | string[] | 불릿(좌=빨강 마커, 우=초록 마커) |

> `left`/`right`는 객체. (duo의 `left`/`right` fallback과는 별개 — versus는 항상 `left`/`right` 사용)

### matrix
```json
{ "archetype": "matrix", "data": {
  "kicker": "비교표", "title": "기준 × 옵션",
  "headers": ["기준", "A", "B"],
  "rows": [ ["속도", "높음", "낮음"], ["비용", "낮음", "높음"] ]
} }
```
| 키 | 타입 | 설명 |
|---|---|---|
| `headers[]` | string[] | 헤더 행(첫 칸 좌측정렬, 나머지 중앙) |
| `rows[]` | array | 각 행: **배열** 또는 `{ "cells": [...] }`(둘 다 허용) |

### rank
```json
{ "archetype": "rank", "data": {
  "kicker": "순위", "title": "순위 변동",
  "rows": [
    { "rank": 1, "label": "항목 A", "delta": "▲2", "highlight": true },
    { "rank": 2, "label": "항목 B", "delta": "—" }
  ]
} }
```
| 항목 키 | 타입 | 설명 |
|---|---|---|
| `rank` | number | 순위(생략 시 인덱스+1) |
| `label` | string | 항목명 |
| `delta` | string | 변동. `▲`→초록 / `▼`→빨강 / 그 외→회색 |
| `highlight` | bool | 강조 행(파란 칩 + blue-faint 카드) |

---

## 7. Field 패밀리 (`header()` 사용)

### quadrant
```json
{ "archetype": "quadrant", "data": {
  "kicker": "2×2", "title": "판단 기준",
  "x_axis": "가로축", "y_axis": "세로축",
  "cells": [
    { "label": "Q1", "heading": "제목", "bullets": ["요점"] },
    { "label": "Q2", "heading": "제목", "body": "설명" }
  ]
} }
```
| 키 | 타입 | 설명 |
|---|---|---|
| `cells[]` | array | 최대 4셀. 각 셀 `{ label, heading, bullets \| body }` |
| `x_axis` / `y_axis` | string | 축 라벨(가장자리) |

### map
```json
{ "archetype": "map", "data": {
  "kicker": "포지셔닝", "title": "2축 맵",
  "x_axis": "가로축", "y_axis": "세로축",
  "points": [
    { "x": 0.2, "y": 0.8, "label": "A" },
    { "x": 0.7, "y": 0.4, "label": "B", "highlight": true }
  ]
} }
```
| 점 키 | 타입 | 설명 |
|---|---|---|
| `x` / `y` | number(0~1) | 정규화 좌표(좌하단 원점). 생략 시 0.5 |
| `label` | string | 점 라벨 |
| `highlight` | bool | 강조점(주황) |

---

## 8. Structure 패밀리 (`header()` 사용)

### flow
```json
{ "archetype": "flow", "data": {
  "kicker": "프로세스", "title": "단계",
  "steps": [ { "heading": "1단계", "body": "설명" }, { "heading": "2단계", "body": "설명" } ]
} }
```
| 스텝 키 | 타입 | 설명 |
|---|---|---|
| `heading` | string | 단계 제목 |
| `body` | string | 단계 설명(선택). 번호·화살표 자동 |

### system
```json
{ "archetype": "system", "data": {
  "kicker": "구조", "title": "시스템 구조",
  "core": "중심",
  "nodes": [ { "label": "노드 A" }, "노드 B(문자열도 가능)" ]
} }
```
| 키 | 타입 | 설명 |
|---|---|---|
| `core` | **string** | 중심 노드 라벨(기본 "Core"). **객체 아님 — 문자열만** |
| `nodes[]` | array | `string` 또는 `{ "label": "..." }`. 좌/우로 자동 분배 |

> 핸드오프 초안의 `core: { heading, body }`(객체)는 **오류** — 실제 빌더는 `core`를 문자열로 읽는다(`shape_text(cb, d.get("core","Core"))`). 노드도 `heading/body`가 아니라 `label`만 읽는다.

---

## 9. Data 패밀리 (`header()` 사용 · `chart()` 기반)

Data 6종은 `data` 전체를 `chart()` spec으로 넘긴다(`spec = dict(d)`). 따라서 `categories`/`series`/`values` 등 차트 키가 `data`에 바로 들어간다. 각 아키타입은 **`type` 기본값**만 다르다(아래). `type`을 명시하면 §10의 어떤 차트로도 바꿀 수 있다.

### share (구성비)
```json
{ "archetype": "share", "data": {
  "kicker": "구성", "title": "점유율",
  "categories": ["A", "B", "C", "D"], "values": [40, 30, 20, 10]
} }
```
- 기본 `type: doughnut`. `categories[]` + `values[]`(또는 `series[0].values`). 우측 범례(색칩+라벨+값) 자동.

### bars (항목 비교)
```json
{ "archetype": "bars", "data": {
  "title": "항목 비교",
  "categories": ["A", "B", "C"], "series": [ { "name": "값", "values": [10, 20, 30] } ]
} }
```
- 기본 `type: bar_clustered`.

### trend (시계열)
```json
{ "archetype": "trend", "data": {
  "title": "추이",
  "categories": ["1월","2월","3월"],
  "series": [ { "name": "Organic", "values": [10, 18, 27] } ]
} }
```
- 기본 `type: line` (시리즈 2개 이상이면 `line_markers`).

### spread (분포)
```json
{ "archetype": "spread", "data": {
  "title": "분포",
  "categories": ["0-10","10-20","20-30"], "values": [3, 12, 25]
} }
```
- 기본 `type: column_clustered`, 범례 off(히스토그램 표현).

### correlate (상관)
```json
{ "archetype": "correlate", "data": {
  "title": "산점도",
  "points": [ { "x": 0, "y": 0 }, { "x": 1, "y": 2.4 } ]
} }
```
- 기본 `type: xy_scatter` (어떤 점에 `size`가 있으면 `bubble`). `points[]`: `{ x, y, size? }`.

### kpi (빅넘버 카드)
```json
{ "archetype": "kpi", "data": {
  "kicker": "KPI", "title": "핵심 지표",
  "items": [
    { "value": "1,200", "label": "첫 번째 지표", "note": "보조 설명" },
    { "value": "4만", "label": "두 번째 지표" }
  ]
} }
```
| 키 | 타입 | 설명 |
|---|---|---|
| 카드 배열 | array | **권장 `items`** · 호환 `kpis` · `stats`(셋 다 허용 — Set·List와 키 일관) |
| 항목 `value` | string | 큰 숫자 |
| 항목 `label` | string | 라벨(대문자) |
| 항목 `note` | string | 보조 설명(선택) |

> `items` 동작은 `build_kpi()`가 `d.get("kpis") or d.get("stats") or d.get("items", [])`로 폴백(커밋 1fb9c3c)하기에 가능. KPI 핸드오프(8f711df7…)와 정합.

---

## 10. 차트 입력 스키마 (`chart()` 헬퍼)

Data 아키타입 `data` 또는 `type` 오버라이드로 접근. 공통 키:

| 키 | 타입 | 설명 |
|---|---|---|
| `type` | string | 차트 종류(아래 목록). 아키타입별 기본값 있음 |
| `categories[]` | string[] | 카테고리 축 라벨 |
| `series[]` | array | `{ "name": "...", "values": [..] }`. 색=팔레트 램프 순환 |
| `values[]` | number[] | 단일 시리즈 단축(= `series:[{name:series_name, values}]`) |
| `series_name` | string | `values` 단축 사용 시 시리즈명 |
| `legend` | bool | 범례 표시(기본: 시리즈 2개 이상이면 자동 on) |
| `number_format` | string | 값 표시 포맷 |
| `points[]` | array | xy/bubble용 `{ x, y, size? }` |

**type 목록**
- 네이티브(python-pptx): `column_clustered` · `column_stacked` · `column_stacked_100` · `bar_clustered` · `line` · `line_markers` · `area` · `pie` · `doughnut` · `radar` · `xy_scatter` · `bubble`
- 합성(도형): `waterfall` · `funnel` · `gauge`(=`progress`) · `gantt`(=`timeline`) · `tam_sam_som` · `bullet` · `slope` · `kpi_cards`
- 데이터 없으면 "차트 데이터 없음" 플레이스홀더(파이/스캐터/xy 동일).

---

## 11. 미디어 입력 스키마 (`media()` 헬퍼)

```json
{ "src": "/mnt/c/.../image.png", "fit": "cover", "caption": "캡션", "focal": "center" }
```
| 키 | 타입 | 설명 |
|---|---|---|
| `src` | string | 이미지 경로. 절대경로 또는 **spec.json 기준 상대경로**. `/mnt/c/...` 권장 |
| `fit` | `"cover"`\|`"contain"` | cover=크롭 채움(기본) / contain=레터박스 |
| `caption` | string | 하단 작은 캡션(선택) |
| `focal` | string | 크롭 초점(기본 `center`) |
| `label` | string | 플레이스홀더 라벨(src 없을 때 표시) |

- `src` 없음/빈 dict `{}`/파일 부재 → **플레이스홀더 박스**(이모지 없음, 비율 힌트).
- 카드의 `image` 키는 **존재 자체**로 이미지 카드 전환(빈 `{}`도 플레이스홀더 카드).

---

## 12. alias 정책 (요약)

| 권장 키 | 허용 alias | 적용 위치 |
|---|---|---|
| `archetype` | `variant` | slides[] 라우팅 |
| `kicker` | `eyebrow` | 모든 헤더형 슬라이드 |
| `title` | `section_title` | section만 |
| `items` | `left`+`right` | duo |
| `items` | `columns` | trio |
| `items` | `cells` | grid |
| `items` | `kpis` / `stats` | kpi |
| `series[0].values` | `values` | 차트(share/spread 등 단일 시리즈) |

> 신규 작성 시 모두 `items`/`kicker`/`archetype`을 쓰는 게 안전하다. alias는 기존 spec 호환·내부 모델 차이 때문에 존재한다.

---

## 13. 검수용 최소 spec

`references/demo/schema-smoke.spec.json` — 23 아키타입을 각 1장씩 최소 입력으로 담았다.
```bash
cd references
python3 tools/build-template.py /tmp/schema-smoke.pptx --spec demo/schema-smoke.spec.json --look ppt-archival-index-deck
python3 -m markitdown /tmp/schema-smoke.pptx > /tmp/schema-smoke.md   # "데이터 없음" 없어야 정상
```
풀 콘텐츠 데모는 `references/demo/all-archetypes.spec.json`.
