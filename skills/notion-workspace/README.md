# notion-workspace

Notion API를 **직접 호출**하여 데이터베이스, 페이지, 블록, 파일 업로드 등 모든 Notion 작업을 자동화합니다.

MCP 서버 없이 Node.js 모듈(`notion-api.mjs`)로 동작하며, Notion API `2026-03-11` 버전을 사용합니다.

---

## 설치

### 방법 1. 명령어 한 줄 (추천)

PowerShell을 열고 아래 명령어를 붙여넣은 뒤 Enter를 누르세요.

```powershell
irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/notion-workspace/install.ps1 | iex
```

> **PowerShell 여는 방법:** `Win + R` → `powershell` 입력 → Enter

설치 후 **Claude Code를 재시작**하면 됩니다.

---

### 방법 2. 파일 직접 다운로드

1. **[메인 리포](https://github.com/1000ssam/skills-for-teachers)** 로 이동합니다.
   > 이 페이지(개별 스킬 폴더)가 아닌, **메인 리포 첫 화면**으로 가야 합니다.

2. 초록색 **`<> Code`** 버튼 → **`Download ZIP`** 클릭

3. 다운로드된 ZIP 파일 압축 해제

4. 압축 해제한 폴더 안의 `skills\notion-workspace` 폴더를 아래 경로에 복사합니다:
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

---

## 지원 기능

| 카테고리 | 기능 |
|---------|------|
| **검색** | 제목 기반 검색 (페이지/DB 필터) |
| **DB** | 생성, 조회, 수정, 쿼리, 전체 조회 (자동 페이지네이션) |
| **페이지** | 생성, 조회, 수정, 삭제 |
| **블록** | 조회, 추가, 삭제 |
| **파일** | 로컬 파일 업로드, URL 다운로드→업로드, 커버 설정, 이미지 블록 추가 |
| **Upsert** | 단건 (10건 미만), 벌크 (10건 이상, 동시성 15) |
| **헬퍼** | 속성 빌더 (title, richText, number, select 등), 블록 빌더 (heading, paragraph, callout 등) |

### 지원하지 않는 기능 (Notion API 미지원)

- 데이터베이스 뷰 생성
- 노션 폼 생성
- 코멘트 작성

---

## 파일 구조

```
notion-workspace/
├── SKILL.md              ← Claude Code가 읽는 스킬 정의
├── README.md             ← 이 파일
├── install.ps1           ← 설치 스크립트
├── config.json           ← (설치 후 자동 생성) Notion 토큰 저장
└── scripts/
    └── notion-api.mjs    ← Notion API 모듈 (CRUD + 업로드 + Upsert)
```
