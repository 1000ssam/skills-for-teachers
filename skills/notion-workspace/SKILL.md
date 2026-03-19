---
name: notion-workspace
description: "Notion API 통합 스킬. DB/페이지/블록 CRUD, 마크다운 읽기/쓰기, 파일 업로드, 이미지 커버 설정, upsert, 코멘트, 페이지 이동 등 모든 Notion 작업을 notion-api.mjs 모듈로 처리합니다. Use when: (1) 노션에 추가/수정/조회, (2) 노션 DB 생성, (3) 노션 이미지 업로드, (4) 노션 커버 설정, (5) 노션 파일 업로드, (6) Notion API 작업. 트리거: '노션', 'Notion', '노션에', '노션 DB', '노션 페이지', '노션 업로드'."
allowed-tools: Bash(node *), Read, Write, Glob, Grep
---

# Notion Workspace 스킬

Notion API를 `notion-api.mjs` 모듈로 직접 호출하여 DB, 페이지, 블록, 파일 업로드 등 모든 작업을 처리하는 스킬.

## Workflow

모든 노션 작업은 아래 순서를 **반드시** 따른다.

### Step 1. config.json 확인

이 스킬 디렉토리 내 `config.json`을 Read 도구로 확인한다.

**config.json이 없는 경우 (최초 실행):**

사용자에게 Notion Integration Token을 질문한다:

```
"Notion Internal Integration 토큰을 알려주세요. (ntn_으로 시작하는 값)
토큰 발급: https://www.notion.so/profile/integrations → '새 API 통합' → 토큰 복사"
```

사용자가 토큰을 알려주면 이 스킬 디렉토리에 `config.json`을 자동 생성한다:

```json
{
  "token": "ntn_..."
}
```

**config.json이 있으면** 바로 Step 2로 진행한다.

### Step 2. 작업 실행

`notion-api.mjs` 모듈을 import하여 작업을 수행한다.

## API 호출 방법

### `notion-api.mjs` 모듈 (유일한 방법)

모든 Notion API 작업에 이 모듈을 사용한다. MCP는 사용하지 않는다.

```javascript
import { notion } from 'file:///<이 스킬의 scripts 디렉토리>/notion-api.mjs';

// 검색
const results = await notion.search('키워드', { filter: 'database' });

// DB 생성
const db = await notion.createDatabase(parentPageId, '새 DB', '📋', {
  '이름': { title: {} },
  '상태': { select: { options: [{ name: '진행중', color: 'blue' }] } },
});

// 페이지 생성 (DB 내) - prop 헬퍼 사용
const page = await notion.createPage(dbId, {
  '이름': notion.prop.title('홍길동'),
  '상태': notion.prop.select('진행중'),
  '점수': notion.prop.number(95),
});

// ── 페이지 본문 읽기/쓰기 (마크다운 우선) ──
// 읽기: 특수 블록도 <callout>, <database> 등 확장 태그로 반환됨 (누락 없음)
const content = await notion.getPageMarkdown(pageId);

// 쓰기: 마크다운 문자열로 본문 전체 교체 (블록 API 대비 토큰 6배 절약)
await notion.updatePageMarkdown(pageId, '## 섹션 제목\n\n본문 내용\n\n- 항목 1\n- 항목 2');

// 블록 API는 마크다운으로 불가능한 세밀한 조작이 필요할 때만 사용
await notion.appendBlocks(pageId, [notion.block.callout('안내', '📝', 'blue_background')]);

// ── 마크다운 쓰기 시 특수 블록 레퍼런스 ──
// ✅ 읽기/쓰기 모두 지원:
//   <callout icon="📌">내용 **볼드** 가능</callout>
//   <details><summary>토글 제목</summary>토글 내부 내용</details>
//   > 인용문 (quote)
//   --- (divider)
//   - [ ] 미완료 / - [x] 완료 (to_do)
//   | 헤더 | ... | (table)
//   ```lang ... ``` (code)
//   $`E=mc^2`$ (인라인 수식)
//   $$\nE=mc^2\n$$ (수식 블록)
//
// ⚠️ 읽기전용 (쓰기 불가, 블록 API로 대체):
//   bookmark → 읽으면 <unknown alt="bookmark"/> 로 표시
//   embed → 읽으면 <unknown alt="embed"/> 로 표시
//   synced_block → 블록 API 필수

// DB 전체 조회 (자동 페이지네이션)
const allPages = await notion.queryAll(dbId);

// 배치 처리 (동시성 15)
await notion.batch(items, async (item) => {
  await notion.createPage(dbId, { '이름': notion.prop.title(item.name) });
});

// Upsert (단건)
const result = await notion.upsertPage(dbId, '이름', 'title', '홍길동', {
  '이름': notion.prop.title('홍길동'),
  '점수': notion.prop.number(95),
});

// Bulk Upsert (대량, queryAll 캐시 + 동시성 15)
const stats = await notion.bulkUpsert(dbId, '이름', [
  { matchValue: '홍길동', properties: { '이름': notion.prop.title('홍길동'), '점수': notion.prop.number(100) } },
]);

// 파일 업로드
await notion.setCover(pageId, 'C:/path/to/cover.webp');
await notion.addImageBlock(pageId, 'C:/path/to/photo.png');
const uploadId = await notion.uploadFromUrl('https://example.com/img.jpg');

// 코멘트
await notion.createComment(pageId, '코멘트 내용');
const comments = await notion.listComments(pageId);

// 페이지 이동
await notion.movePage(pageId, { page_id: targetPageId });
```

**주의사항**:
- 크리덴셜은 모듈이 `config.json`에서 자동 로드
- API 버전 `2026-03-11` (DB ID → DS ID 자동 변환 내장)

## 실패 시 자가 수복 프로토콜

모듈 함수 호출이 실패하면 아래 순서를 따른다. **MCP 폴백은 절대 하지 않는다.**

1. **에러 분석** — API 응답 코드와 메시지 확인
2. **인라인 스크립트 작성** — 모듈을 import하되, 실패한 부분만 `notion.call()`로 우회
3. **성공 시 모듈 업데이트** — 우회 코드를 `notion-api.mjs`에 반영 + 커밋

## 토큰 절약 규칙

1. **페이지 본문은 마크다운 API 우선**: 읽기 `getPageMarkdown()`, 쓰기 `updatePageMarkdown()`. 특수 블록도 확장 태그로 보존됨. 블록 API 대비 읽기 20배, 쓰기 6배 토큰 절약.
2. **블록 API는 세밀한 조작이 필요할 때만**: 특정 블록 하나만 수정/삭제 등.
3. **여러 페이지 작업 시** `notion.batch()`로 동시성 15 병렬 처리.
4. **전체 조회 시** `notion.queryAll()`로 자동 페이지네이션.
5. **Upsert 전략 선택**: 10건 미만 → `upsertPage()`, 10건 이상 → `bulkUpsert()`.
