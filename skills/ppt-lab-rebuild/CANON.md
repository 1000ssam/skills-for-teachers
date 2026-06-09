# CANON — 방법론 출처와 크레딧

이 프로젝트의 레이아웃 축(그리드 시스템 + 아키타입 분류)은 **공개된 디자인·시각커뮤니케이션 캐논**에서 1차 원리로 도출했다. 아래 저작들은 *방법론적 영감*이며, 본 리포의 모든 좌표·코드·명명·큐레이션은 그 원리를 적용해 **자작**한 것이다.

> 법적 고지: 아래는 **아이디어·방법론**에 대한 크레딧이다. 아이디어·프레임워크·레이아웃 유형(2컬럼, 2×2 매트릭스 등)은 저작권 보호 대상이 아니므로 라이선스 의무는 없다. 그럼에도 학술적·직업적 예의로 출처를 명시한다. 특정 저작물의 *표현*(텍스트·도판·구체적 좌표)은 복제하지 않았다.

## 그리드 시스템

- **Josef Müller-Brockmann**, *Grid Systems in Graphic Design: A Visual Communication Manual* (1961/1981).
  - 차용한 원리: 페이지를 수학적 모듈로 분할, 타입 크기로 결정되는 베이스라인 정렬, 8~32 필드 모듈러 그리드.
  - 적용: `references/grid.json`의 12컬럼 × 8행 모듈러 그리드, baseline 4px, `grid_box()` 파생 좌표.
- **International Typographic Style (스위스 타이포그래피)** — 구조적·일관된 정렬, 비대칭 레이아웃의 질서.

## 시각 커뮤니케이션 / 차트 선택

- **Gene Zelazny**, *Say It With Charts: The Executive's Guide to Visual Communication* (McKinsey).
  - 차용한 원리: 메시지를 5가지 비교유형(**구성·항목·시계열·빈도·상관**)으로 환원하고, 각 유형이 최적 차트형(파이·바·라인·히스토그램·스캐터)에 1:1 대응.
  - 적용: `references/archetypes.md`의 Data family 6 아키타입(`share`·`bars`·`trend`·`spread`·`correlate` + `kpi`).
- **Michael Alley**, *The Craft of Scientific Presentations* — assertion-evidence(한 슬라이드 한 주장 + 근거) 원리.
  - 적용: Focus family(`statement`).

## 자작 범위 (출처와 분리)

- 그리드 수치(마진 96/64, 12×8, 거터·컬럼폭), `grid_box()` 파생식.
- 7 family 그룹핑(Frame·Focus·Set·Contrast·Field·Structure·Data), 아키타입 명명(서술형 슬러그), 의사결정 트리.
- 모든 슬롯 좌표(그리드 파생), 빌드 함수, 미디어 슬롯 동작.

## 흡수된 외부 자산 (별도 라이선스 — `THIRD-PARTY-NOTICES.md` 참조)

레이아웃 축과 무관한 **스타일/룩 축**에는 라이선스 있는 외부 자산이 있다:
- design-pick 110 룩 — **MIT** (출처표기 후 사용).
- velis 테마 — **CC0 1.0** (퍼블릭도메인).
- (이전 실험에서 흡수했던 무료 스톡 덱 파생 스타일·팔레트는 본 클린룸 리포에 **포함하지 않음** — 해당 출처 표기 의무도 없음.)
