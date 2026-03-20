# notion-pilot

Notion API를 **직접 호출**하여 데이터베이스, 페이지, 블록, 파일 업로드, 코멘트 등 모든 Notion 작업을 자동화합니다.

MCP 서버 없이 Node.js 모듈(`notion-api.mjs`)로 동작하며, **최신 Notion API `2026-03-11` 버전**을 사용합니다.

---

## 이 스킬이 특별한 이유

### 마크다운 API 기반 — 토큰 20배 절약

Notion API `2026-03-11`에서 추가된 **마크다운 엔드포인트**를 활용합니다. 기존 블록 API 대비:

- **읽기 20배 절약** — JSON 중첩 구조 대신 마크다운 문자열 반환
- **쓰기 6배 절약** — 블록 객체 조립 대신 마크다운 문자열 전달
- **특수 블록 보존** — 콜아웃, 토글, 수식 등이 확장 태그(`<callout>`, `<details>`, `$$`)로 읽기/쓰기 양방향 지원

LLM과 Notion을 연결할 때 가장 큰 병목이었던 토큰 비용 문제를 해결합니다.

### Bulk Upsert 내장 — 대량 작업 최적화

수십~수백 건의 데이터를 노션 DB에 넣을 때, 기존 데이터가 있으면 업데이트하고 없으면 생성하는 **upsert** 패턴이 내장되어 있습니다.

- **단건 upsert** (`upsertPage`) — 10건 미만, 건당 쿼리
- **벌크 upsert** (`bulkUpsert`) — 10건 이상, DB 전체를 캐시한 뒤 동시성 15로 병렬 처리
- 100건 기준 **33초** (3.0건/초), 429 에러 0건 달성

### DB ID / DS ID 자동 변환

Notion API `2025-09-03`에서 도입된 Data Source 개념을 자동으로 처리합니다. DB ID를 넘기든 DS ID를 넘기든 모듈이 알아서 변환합니다. API 버전 마이그레이션을 신경 쓸 필요가 없습니다.

---

## 설치

### 방법 1. 명령어 한 줄 (추천)

PowerShell을 열고 아래 명령어를 붙여넣은 뒤 Enter를 누르세요.

```powershell
irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/notion-pilot/install.ps1 | iex
```

> **PowerShell 여는 방법:** `Win + R` → `powershell` 입력 → Enter

설치 후 **Claude Code를 재시작**하면 됩니다.

---

### 방법 2. 파일 직접 다운로드

1. **[메인 리포](https://github.com/1000ssam/skills-for-teachers)** 로 이동합니다.
   > 이 페이지(개별 스킬 폴더)가 아닌, **메인 리포 첫 화면**으로 가야 합니다.

2. 초록색 **`<> Code`** 버튼 → **`Download ZIP`** 클릭

3. 다운로드된 ZIP 파일 압축 해제

4. 압축 해제한 폴더 안의 `skills\notion-pilot` 폴더를 아래 경로에 복사합니다:
   ```
   C:\Users\{내 사용자 이름}\.claude\skills\
   ```
   > `.claude` 폴더가 안 보이면: 파일 탐색기 → **보기** → **숨긴 항목** 체크

5. Claude Code 재시작

---

## 사전 준비

### 1. Node.js

이 스킬은 **Node.js**가 필요합니다. 설치되어 있지 않다면:
→ [https://nodejs.org](https://nodejs.org) 에서 **LTS 버전** 다운로드 후 설치

### 2. Notion Internal Integration 토큰

1. [notion.so/profile/integrations](https://www.notion.so/profile/integrations) 접속
2. **"새 API 통합"** 클릭
3. 이름 입력 (예: "Claude Code") → **제출**
4. **Internal Integration Secret** (`ntn_`으로 시작) 복사
5. Integration에 사용할 **노션 페이지/DB를 공유** (페이지 우측 상단 `···` → `연결` → 만든 Integration 선택)
6. 코멘트 기능을 사용하려면: Integration 설정 → **"Read comments"** + **"Insert comments"** 권한 활성화

> 처음 실행하면 Claude Code가 토큰을 물어봅니다. 한 번 설정하면 이후엔 자동으로 기억합니다.

---

## 사용법

Claude Code에서 이렇게 말하면 됩니다:

| 입력 | 동작 |
|------|------|
| `"노션에 DB 만들어줘"` | 데이터베이스 생성 |
| `"노션에 페이지 추가해"` | 페이지 생성 |
| `"노션 DB 조회해줘"` | 데이터베이스 쿼리 |
| `"노션에 이미지 업로드해"` | 파일 업로드 + 블록/커버 설정 |
| `"노션 페이지 수정해"` | 속성 업데이트 |
| `"노션 페이지 내용 읽어줘"` | 마크다운으로 본문 조회 |
| `"노션에 글 써줘"` | 마크다운으로 본문 작성 |
| `"노션 페이지 이동해"` | 다른 부모로 이동 |

---

## 지원 기능

| 카테고리 | 기능 |
|---------|------|
| **검색** | 제목 기반 검색 (페이지/DB 필터) |
| **DB** | 생성, 조회 (DS 자동 변환), 수정, 쿼리, 전체 조회 (자동 페이지네이션) |
| **페이지** | 생성 (DB ID/DS ID 모두 허용), 조회, 수정, 삭제, 이동 |
| **마크다운** | 페이지 본문 읽기/쓰기 (블록 API 대비 읽기 20배, 쓰기 6배 토큰 절약) |
| **블록** | 조회, 추가, 삭제 (마크다운으로 불가능한 세밀한 조작 시) |
| **파일** | 로컬 파일 업로드, URL 다운로드→업로드, 커버 설정, 이미지 블록 추가 |
| **Upsert** | 단건 (10건 미만), 벌크 (10건 이상, queryAll 캐시 + 동시성 15) |
| **코멘트** | 생성, 목록 조회, 단건 조회 |
| **헬퍼** | 속성 빌더 13종 (title, richText, number, select, multiSelect, status, checkbox, date, url, email, phone, people, relation), 블록 빌더 15종 (paragraph, heading1/2/3, bullet, numbered, toDo, quote, toggle, callout, code, bookmark, equation, divider, tableOfContents) |

### 마크다운 쓰기 시 지원되는 특수 블록

| 문법 | 노션 블록 |
|------|----------|
| `<callout icon="📌">내용</callout>` | 콜아웃 |
| `<details><summary>제목</summary>내용</details>` | 토글 |
| `> 인용문` | 인용 |
| `---` | 구분선 |
| `- [ ]` / `- [x]` | 체크박스 |
| `\| 테이블 \|` | 테이블 |
| ` ```lang ``` ` | 코드 블록 |
| `$\`수식\`$` | 인라인 수식 |
| `$$` + 수식 + `$$` | 수식 블록 |

### 지원하지 않는 기능

- 데이터베이스 뷰 생성 (Notion API 미지원)
- 노션 폼 생성 (Notion API 미지원)
- 마크다운으로 bookmark/embed 쓰기 (읽기는 가능, 쓰기는 블록 API로 대체)

---

## 파일 구조

```
notion-pilot/
├── SKILL.md              ← Claude Code가 읽는 스킬 정의
├── README.md             ← 이 파일
├── install.ps1           ← 설치 스크립트
├── config.json           ← (설치 후 자동 생성) Notion 토큰 저장
└── scripts/
    └── notion-api.mjs    ← Notion API 모듈 (~600줄)
                             CRUD + 마크다운 + 파일 업로드 + Upsert + 코멘트
```
