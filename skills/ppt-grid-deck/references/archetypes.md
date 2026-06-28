# 아키타입 분류 — 1차 원리 씨앗(24) + 레퍼런스 흡수로 성장

> **입력 스키마**: 이 문서는 아키타입의 *과업·슬롯·도출 근거*를 다룬다. spec.json `data`에 넣을 **실제 입력 키**(필수/선택/alias·최소 예시)는 [`spec-schema.md`](spec-schema.md) 참조.

> **출처 원칙**: 이 분류는 "검증된 카탈로그"를 통째로 상속하지 않고, *덱이 수행하는 커뮤니케이션 과업*에서 1차 원리로 도출했다. 각 아키타입은 ① 어떤 과업을 푸는지, ② 근거 캐논, ③ 그리드 슬롯 구성으로 정의된다. 보편 과업(표지·비교·사분면)과 결과가 수렴하는 건 정상이며 저작권 대상도 아니다 — 원본성은 *도출·명명·그리드 구성*에 있다.
>
> **카탈로그는 닫혀있지 않다(흡수로 성장).** 이 24는 *씨앗*이며, 레퍼런스 덱에서 기존과 안 겹치는 *진짜 새 구조*를 만나면 `extract-pptx.py`+`grid-snap.py`로 측정·라우팅해 신규 아키타입으로 흡수한다(rebuild 경로 = `grid.json` 슬롯 + `gen-layouts.py` 재생성 + `build_<name>()` + 이 문서 등록). 단 **좌표는 항상 자작 `grid.json` 파생**이고 통째 카탈로그를 상속하지 않는다는 점은 불변(= 그 한정 의미의 "클린룸").
> **명명**: 상속 코드(C/2C/SWOT/AR…) 폐기. 자체 서술형 슬러그 사용(명시적 > 영리한).
> **좌표**: 전부 `grid.json`의 `grid_box(c0, cspan, r0, rspan)`에서 파생. 아래 슬롯의 `grid:[...]`가 그 인자.

---

## 도출 축 — "이 슬라이드가 푸는 과업은?"

```
덱의 뼈대/길찾기인가?        → Frame   (cover · section · agenda · closing)
한 가지 메시지에 집중?        → Focus   (statement · feature · showcase)
여러 항목을 나열(비교 아님)?  → Set     (duo · trio · grid · list)
명시적으로 비교?             → Contrast(versus · matrix · rank)
2축 위에 배치?              → Field   (quadrant · map)
순서·구조를 보여줌?          → Structure(flow · system)
데이터가 주인공?            → Data    (share · bars · trend · spread · correlate · kpi)
```

도출 근거:
- **Frame/Focus/Set/Contrast/Field/Structure** 6과업: 프레젠테이션 정보설계의 보편 관계 유형(나열·비교·위치·과정·구조). 단일 출처 카탈로그가 아니라 정보설계 일반론에서 옴.
- **Data 6종**: Gene Zelazny, *Say It With Charts* — 메시지를 5 비교유형(구성·항목·시계열·빈도·상관)으로 환원하고 각자 최적 차트형이 1:1 대응. 여기에 KPI 대시보드(다수 단일지표) 추가.
- **2×2/맵**: 연속 2축(map) vs 범주 2축(quadrant) 구분은 좌표계 차원의 문제(정보설계). 특정 프레임워크(SWOT/BCG)는 *내용*이지 아키타입이 아니다 → 범용 quadrant에 내용으로 채움.

---

## Family 1 — Frame (덱 뼈대 / 길찾기)

헤더밴드 미사용(자체 전면 구도). 색·배경은 룩/팔레트가 결정.

| 슬러그 | 과업 | 슬롯 (grid_box 인자) |
|---|---|---|
| `cover` | 덱 오프닝(제목+맥락) | kicker `[0,8,1,1]` · title `[0,11,2,3]` · subtitle `[0,9,5,1]` · meta `[0,9,7,1]` |
| `section` | 섹션 전환 | index `[0,2,1,1]` · section_title `[0,10,3,2]` · caption `[0,8,5,1]` |
| `agenda` | 목차/어젠다 | kicker `[0,6,0,1]` · title `[0,10,1,1]` · items[] `[0,12,3,4]`(행 분배) |
| `closing` | 마무리/CTA | kicker `[0,8,1,1]` · title `[0,11,2,2]` · subtitle `[0,9,4,1]` · cta `[0,4,6,1]` |

근거: 모든 덱은 열고(cover)·구획하고(section)·안내하고(agenda)·닫는다(closing). 보편 뼈대.

## Family 2 — Focus (단일 메시지)

헤더밴드 사용.

| 슬러그 | 과업 | 슬롯 |
|---|---|---|
| `statement` | 한 주장 + 근거 | lead `[0,9,2,1]`(body_top) · support[] `[0,11,3,3]` |
| `feature` | 히어로 비주얼 + 인사이트 | body `[0,6,2,4]`(좌) · media `[7,5,2,5]`(우 패널/이미지) |
| `showcase` | 좌측정렬 미디어 + 불릿(비율 자동배치) | media 영역 `[0,12,2,5]`; 이미지 좌측정렬·무크롭, 불릿은 종횡비로 우측/하단 자동 |

근거: assertion-evidence(Michael Alley) — 한 슬라이드 한 주장. `feature`는 텍스트-이미지 2분할(보편). `showcase`는 미디어가 곧 메시지일 때(가이드·UI 캡처·도표 원본) **헤더와 좌측정렬·무크롭**으로 크게 싣고, 불릿은 **이미지 종횡비가 자동 결정**(세로 여유=우측 / 가로 여유=하단) — 사용자 분기 불필요. feature의 우측 반쪽 cover와 직교하는 선택.

## Family 3 — Set (병렬 나열, 비교 아님)

헤더밴드 사용. 항목은 동등 카드(`card()` 헬퍼).

| 슬러그 | 과업 | 슬롯 |
|---|---|---|
| `duo` | 2개 동등 항목 | item_l `[0,6,2,5]` · item_r `[6,6,2,5]` |
| `trio` | 3개 동등 항목 | col1 `[0,4,2,5]` · col2 `[4,4,2,5]` · col3 `[8,4,2,5]` |
| `grid` | 4~6개 카드 | cells[] (2×2 또는 2×3, presets quarter/third × 2행) |
| `list` | 순차 리스트/메뉴 | items[] `[0,12,2,5]`(행 분배, 번호/불릿) |

근거: 나열은 비교가 아님(서열·대비 의도 없음). 2·3·N 분할은 12컬럼의 자연 분할(2·3·4·6).

**🖼 이미지 카드 변종(수업용 핵심)**: `duo`/`trio`/`grid` 각 카드는 상단에 **선택적 이미지 밴드**(`image` 미디어 슬롯)를 가질 수 있다. 카드 = 이미지(상) + heading/body(하). 카드별로 `image`가 있으면 이미지 카드, 없으면 텍스트 카드(혼용 가능). → "두 컬럼 각각 사진+설명" 수업 레이아웃이 `duo`(이미지 카드)로 바로 나온다. 이미지 밴드는 카드 박스 상단 ~55% 높이, heading/body는 하단. 자세한 동작은 아래 "이미지·미디어 슬롯".

## Family 4 — Contrast (명시적 비교)

| 슬러그 | 과업 | 슬롯 |
|---|---|---|
| `versus` | A vs B / Before·After | left{label,points} `[0,6,2,5]` · right{label,points} `[6,6,2,5]` · (중앙 vs 마크) |
| `matrix` | 기준 × 옵션 표 | table `[0,12,2,5]`(헤더행 + N행) |
| `rank` | 서열/변동 | rows[]{rank,label,delta} `[0,10,2,5]` |

근거: 비교는 "대비 의도"가 핵심(Set과 구분). `versus`=2자 대립, `matrix`=다기준 정식비교, `rank`=서열. Zelazny 항목비교의 정성 버전.

## Family 5 — Field (2축 공간 배치)

| 슬러그 | 과업 | 슬롯 |
|---|---|---|
| `quadrant` | 범주 2×2 | x_axis · y_axis · cells[4] `[0,12,2,5]`를 2×2 분할 |
| `map` | 연속 2축 포지셔닝 | x_axis · y_axis · plot `[0,9,2,5]` · points[]{x:0~1,y:0~1,label} |

근거: 좌표계 차원 문제 — 범주축(quadrant) vs 연속축(map). SWOT·BCG·아이젠하워는 *내용*으로 quadrant에 주입.

## Family 6 — Structure (과정 / 구조)

| 슬러그 | 과업 | 슬롯 |
|---|---|---|
| `flow` | 순서/단계/타임라인 | steps[]{heading,body} `[0,12,3,3]`(가로 분배 + 커넥터) |
| `system` | 아키텍처/계층 | core(중심) `[4,4,4,2]` · nodes[] (코어 주위 그리드 셀에 배치) |

근거: 과정(선형 순서)과 구조(중심-노드 관계)는 다른 관계. `system`의 노드 배치는 그리드 셀 파생(상속 오빗 수학 폐기).

## Family 7 — Data (Zelazny 5비교유형 + KPI)

헤더밴드 + 차트영역. 차트는 python-pptx `add_chart` 또는 도형 합성.

| 슬러그 | Zelazny 비교유형 | 차트형 | 슬롯 |
|---|---|---|---|
| `share` | 구성(component) | 파이/도넛/누적 | chart `[0,7,2,5]` · legend `[8,4,2,5]` |
| `bars` | 항목(item) | 가로/세로 바 | chart `[0,12,2,5]` |
| `trend` | 시계열(time-series) | 라인/세로열 | chart `[0,12,2,5]` |
| `spread` | 빈도(frequency) | 히스토그램 | chart `[0,12,2,5]` |
| `correlate` | 상관(correlation) | 스캐터/버블 | chart `[0,10,2,5]` |
| `kpi` | (다수 단일지표) | 빅넘버 카드 N | cells[] `[0,12,2,3]`(가로 N분할) |

근거: Zelazny의 메시지→비교유형→차트형 1:1 매핑. 데이터 아키타입은 캐논이 가장 강함(저자 공개 프레임워크).

**`kpi` 입력 키**: KPI 카드 배열은 `items`(권장) · `kpis` · `stats` 중 하나로 받는다. `items`가 권장 기본형(agenda·duo·trio·grid·list와 키 일관). 기존 호환을 위해 `kpis`·`stats`도 유지. 각 항목: `{value, label, note?}`.

---

## 이미지·미디어 슬롯 (slot fill 종류 — 아키타입 아님)

이미지는 별도 아키타입이 아니라 **슬롯을 채우는 종류**다. `feature`의 `media`, Set 카드의 `image`가 미디어 슬롯이며, 한 가지 헬퍼 `media(slide, box, spec, fit)`로 처리한다.

**spec 키**: `{ "src": "경로|null", "fit": "cover|contain", "caption": "옵션", "focal": "center|top|..." }`

**동작**:
- `src` 있고 파일 존재 → **실제 이미지 삽입**(python-pptx `add_picture`). 슬롯 박스에 맞춤:
  - `cover`(기본): 박스를 꽉 채우고 넘치는 부분 크롭(`picture.crop_*` 또는 PIL 전처리). 사진·자료에 적합.
  - `contain`: 비율 유지 레터박스(도표·로고에 적합, 잘림 방지).
- `src` 없음/누락 → **플레이스홀더**: `slate-50` 채움 + 1px 테두리 박스, 중앙에 라벨("이미지 자리" + 권장 비율 같은 힌트) + 단순 도형 아이콘(이모지 금지, 도형만). 실제 작업에서 자리만 잡아두고 나중에 교체.
- `caption` 있으면 박스 하단에 캡션(작은 글씨). 출처표기용으로도 사용.

**경로 규칙(WSL)**: 이미지 경로는 `/mnt/c/...` 마운트 경로 사용. spec의 상대경로는 spec 파일 기준 해석.

**적용 아키타입**: `feature`(media, 큰 1장) · `duo`/`trio`/`grid`(카드별 image) · `statement`(선택적 보조 image) · `cover`/`section`(선택적 풀블리드/사이드 배경 — 룩이 다크 캔버스를 줄 때).

---

## 출처 / 크레딧

방법론 출처는 리포 `CANON.md`에 별도 명시(라이선스 의무는 아니나 떳떳이 밝힘):
- **Gene Zelazny, *Say It With Charts*** — Data family의 5비교유형→차트형 매핑.
- **Josef Müller-Brockmann, *Grid Systems in Graphic Design*** — 그리드 모듈·베이스라인.
- 프레임워크·아이디어는 저작권 대상이 아니며, 좌표·코드·명명·구성은 전부 자작.

---

## 합계

7 family · **24 아키타입** (Frame 4 · Focus 3 · Set 4 · Contrast 3 · Field 2 · Structure 2 · Data 6).

## 구 분류와의 매핑(참고 — 코드 재사용 아님, 폐기 확인용)

상속 20유형은 이 분류에 *수렴*하지만(보편 과업), 코드·슬롯·좌표·그룹핑·의사결정트리는 전부 신규. 예: 구 `2C`→`duo`, `3`→`trio`, `W`(SWOT)→`quadrant`+내용, `AR`→`system`(오빗수학 폐기·그리드 파생), `GD`→`share`. **상속 코드/좌표는 신규 리포에 존재하지 않음.**
