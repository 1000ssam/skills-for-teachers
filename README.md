# skills-for-teachers

한국 학교 교사를 위한 **Claude Code 스킬** 모음입니다.

공문서 정리, 수능 기출 분석, 인수인계서 작성, 교과세특 초안 작성 등 학교 행정·교육 업무를 자동화합니다.

---

## 스킬 목록

| 스킬 | 설명 | 자세히 |
|------|------|--------|
| **document-organizer** | 공문서 파일을 공문번호별로 자동 분류 | [README](skills/document-organizer/README.md) |
| **exam-analyzer** | 교과서 단원 × 수능 기출 매칭 → 분석표 + 문항 스크린샷 | [README](skills/exam-analyzer/README.md) |
| **handover-generator** | 공문 파일명 분석 → 업무 인수인계서 자동 생성 | [README](skills/handover-generator/README.md) |
| **student-record-writer** | 학생 산출물·관찰 메모 → 교과세특 초안 작성 | [README](skills/student-record-writer/README.md) |
| **student-record-pipeline** | 한 반 활동지(스캔·사진·파일) → 교과세특 초안 한꺼번에 만들기 (학생별 짝짓기 → 형광펜 → 문장 만들기 → 점검 → NEIS에 넣기) | [README](skills/student-record-pipeline/README.md) |
| **notion-pilot** | Notion API 통합 (DB/페이지/블록 CRUD, 파일 업로드, Upsert) | [README](skills/notion-pilot/README.md) |
| **youtube-scraper-setup** | 유튜브 채널 RSS 스크래퍼 프로젝트 자동 세팅 (Notion DB + 자막 수집) | [README](skills/youtube-scraper-setup/README.md) |
| **ppt-grid-deck** | 그리드 기반으로 수업 자료·발표 덱 PPTX 자동 생성 (32 완성본 디자인 룩) | [README](skills/ppt-grid-deck/README.md) |

---

## 전체 설치 (모든 스킬 한 번에)

### macOS / Linux

터미널을 열고 아래 명령어를 붙여넣은 뒤 Enter를 누르세요.

```bash
curl -fsSL https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/install.sh | bash
```

> **터미널 여는 방법 (Mac):** `Cmd + Space` → `터미널` 입력 → Enter

### Windows

PowerShell을 열고 아래 명령어를 붙여넣은 뒤 Enter를 누르세요.

```powershell
irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/install.ps1 | iex
```

> **PowerShell 여는 방법:** `Win + R` → `powershell` 입력 → Enter

설치가 완료되면 **Claude Code를 재시작**하면 됩니다.

---

## 스킬 하나만 설치하고 싶다면

각 스킬의 README에서 개별 설치 명령어를 확인하세요.

---

## Claude Code가 없다면?

스킬을 사용하려면 **Claude Code**가 먼저 설치되어 있어야 합니다.
→ [Claude Code 설치 방법](https://docs.anthropic.com/ko/docs/claude-code)

---

## 변경 로그

### 2026-08-01 — student-record-pipeline 다시 올림 + 형광펜 화면 새로 만듦

만들던 중이라 잠시 내려 뒀던 스킬을 다시 올렸습니다. 전체 설치·단독 설치 양쪽 다 이 스킬이 포함됩니다.

- **형광펜 화면을 새로 만들었습니다.** 학생 카드가 세로로 길게 쌓이던 것을 없애고, 왼쪽 학생 목록 + 작업 영역으로 바꿨습니다. 형광펜 칠하는 화면과 초안을 읽고 판정하는 화면을 나눴고, 칠하는 화면은 `원문 / 주석 / 총평` 세 칸이라 위아래로 오갈 일이 없습니다. 키보드로도 넘길 수 있습니다.
- 초안이 나온 학생은 파랑, 확정한 학생은 초록으로 목록에 표시됩니다.
- 짝짓기·명렬표·설정 예시 파일 4개가 공개본에 빠져 있던 것을 채웠습니다.

### 2026-07-15 — student-record-pipeline 스킬 추가

한 반 활동지를 모아 교과세특 초안을 한꺼번에 만드는 스킬을 추가했습니다. 먼저 과제와 채점 기준을 묻고,
활동지에서 학생 글을 읽어들여(파일 그대로 / OCR / AI가 사진 보고 옮겨 적기), 명렬표와 맞춰 학생별로 짝지은 뒤,
깨진 글자를 되살리고, 초안을 쓰고, 자동 점검을 거쳐, NEIS 엑셀이 있으면 확정본을 그 파일에 되돌려 넣습니다.
모든 규칙은 2026 기재요령·2022 개정 교육과정·KICE 예시집에서 가져왔습니다.

### 2026-03-26 — notion-pilot `notion-api.mjs` 주요 수정

**Notion API 2026-03-11 대응 + 사일런트 에러 검증 추가**

- `createDatabase`: `POST /databases`가 properties를 무시하는 문제 수정. DB 생성 후 `PATCH /data_sources/{dsId}`로 properties를 별도 추가하는 방식으로 변경.
- `updateDatabase`: properties 변경 시 `/data_sources/` 경로로 라우팅하도록 수정.
- `createPage`, `updatePage`: 쓰기 후 반환값에서 요청한 속성 존재 여부를 검증, 누락 시 에러를 throw하여 사일런트 실패 방지.

---

## 라이선스

MIT License — 저작권자 1000쌤(@iooo_tttt). 전문은 [`LICENSE`](LICENSE).

**함께 실린 남의 것**은 [`LICENSES/`](LICENSES) 에 각각의 고지를 둡니다.

| 파일 | 출처 | 라이선스 |
|---|---|---|
| `skills/student-record-pipeline/references/achievement-standards-2022.csv` | [gepai-mcp](https://github.com/pblsketch/gepai-mcp) | [MIT](LICENSES/gepai-mcp-MIT.txt) |
| `skills/ppt-grid-deck` 의 디자인 룩 | [Design Diversity](https://github.com/epoko77-ai/design-diversity) | MIT (각 룩 항목에 출처 기록) |
