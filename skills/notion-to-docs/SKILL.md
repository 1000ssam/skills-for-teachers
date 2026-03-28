---
name: notion-to-docs
description: "Notion 페이지를 Google Docs로 변환합니다. 단건 또는 DB 일괄 변환 지원. Use when: (1) 노션 문서 변환, (2) 노션→구글독스, (3) Notion to Docs, (4) 독스로 변환, (5) 구글 독스로 변환. 트리거: '노션 문서 변환', '구글독스로 변환', '노션 변환', '독스로', 'notion to docs'."
allowed-tools: Bash(node *), Read, Write, Glob
---

# Notion → Google Docs 변환 스킬

노션 페이지를 Google Docs로 즉시 변환한다. 마크다운 우선 + 블록 API 보충 하이브리드 방식.

## Workflow

### Step 1. config.json 확인

이 스킬 디렉토리 내 `config.json`을 Read 도구로 확인한다.

**config.json이 없는 경우 (최초 실행):**

`config.example.json`을 복사하여 `config.json`을 생성한다:

```json
{
  "notion_token": ""
}
```

그 다음 Step 2로 진행한다.

**config.json이 있고 notion_token이 채워져 있으면** Step 3으로 진행한다.

### Step 2. Notion 토큰 설정 (최초 1회)

사용자에게 안내:

```
Notion 토큰이 필요합니다.

1. https://www.notion.so/profile/integrations 에서 '새 API 통합'을 생성하세요
2. 변환할 페이지가 있는 워크스페이스에 통합을 연결하세요
3. 토큰(ntn_으로 시작)을 여기에 붙여넣어 주세요
```

사용자가 토큰을 붙여넣으면 → config.json의 `notion_token`에 저장한다.

### Step 3. Google 인증 확인

이 스킬 디렉토리에 `token.json`이 존재하는지 확인한다.

**token.json이 없는 경우 (최초 실행):**

사용자에게 안내:

```
Google 계정을 연결합니다. 브라우저가 열리면 Google 로그인 후 권한을 허용해 주세요.
```

실행:
```bash
node <이 스킬의 scripts 디렉토리>/google-auth.js --setup
```

브라우저가 열리고 사용자가 권한을 허용하면 `token.json`이 자동 저장된다.

**token.json이 있으면** 바로 Step 4로 진행한다 (토큰 갱신은 자동).

### Step 4. 입력 파악

사용자 입력에서 노션 URL 또는 ID를 추출한다.

**페이지 URL 패턴:**
- `https://www.notion.so/워크스페이스/페이지제목-{pageId}`
- `https://www.notion.so/{pageId}`
- 직접 ID: `318dd1dc-d644-80b7-beb6-c98bad30b9ac`

**DB URL 패턴:**
- `https://www.notion.so/워크스페이스/{dbId}?v=...`
- DB ID를 직접 전달

**모드 판별:**
- URL에 `?v=` 파라미터가 있으면 → DB → 일괄 변환
- 그 외 → 페이지 → 단건 변환

### Step 5. 변환 실행

**단건 페이지 변환:**
```bash
node <이 스킬의 scripts 디렉토리>/convert.js <page-id>
```

**DB 하위 페이지 일괄 변환:**
```bash
node <이 스킬의 scripts 디렉토리>/batch-convert.js <db-id>
```

### Step 6. 결과 보고

변환 완료 후 Google Docs URL을 사용자에게 보고한다.
- 단건: URL 1개
- 일괄: 페이지별 URL 목록

## 스타일 설정

스타일은 `scripts/style-map.js`에서 관리한다.

| Notion 블록 | Google Docs |
|---|---|
| H1 | Arimo 굵게 25pt |
| H2 | Arimo 굵게 16pt |
| H3 | Arimo 굵게 14pt 파랑 |
| H4 | Arimo 굵게 12pt 파랑+밑줄 |
| 본문 | Arimo 10pt, 줄간격 150% |
| 글머리 기호 | ●○■ |
| 번호 목록 | 1.a.i. |
| 인용 | 이탤릭, 좌측 회색 테두리 |
| 콜아웃 | Notion 색상별 배경색 |
| 코드 | JetBrains Mono 9pt, 회색 배경 |

## 주의사항

- Notion 이미지 URL은 1시간 만료 — 변환 즉시 실행해야 함
- Google OAuth 토큰은 자동 갱신됨 (refresh_token)
- `<unknown>` 블록(bookmark, embed 등)은 블록 API로 자동 보충
