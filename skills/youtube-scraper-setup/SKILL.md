---
name: youtube-scraper-setup
description: "YouTube RSS 스크래퍼 프로젝트를 처음부터 세팅합니다. 환경 점검, Notion Integration 생성, DB 구성(자동생성/템플릿복제/기존DB), 스크립트 스캐폴딩, OS 스케줄러 등록까지 대화형으로 안내합니다. Use when: (1) 유튜브 스크래퍼 세팅, (2) YouTube scraper 설정, (3) 유튜브 스크랩 프로젝트 생성, (4) 영상 수집 자동화 세팅. 트리거: '유튜브 스크래퍼 만들어줘', 'YouTube scraper 세팅', '유튜브 스크랩 프로젝트', '영상 수집 자동화'"
---

# YouTube Scraper Setup

YouTube 채널 RSS 피드를 모니터링하여 신규 영상의 자막을 수집하고 Notion DB에 저장하는 프로젝트를 세팅하는 스킬.

모든 단계를 순서대로 수행한다. 건너뛰지 않는다.

## 유틸: Notion URL → ID 파싱

유저에게 Notion ID를 직접 요구하지 않는다. 항상 URL을 받아서 파싱한다.

```javascript
function parseNotionId(url) {
  const clean = url.replace(/[?#].*$/, '').replace(/-/g, '');
  const match = clean.match(/([a-f0-9]{32})$/);
  if (!match) throw new Error('Notion URL에서 ID를 추출할 수 없습니다: ' + url);
  const h = match[1];
  return `${h.slice(0,8)}-${h.slice(8,12)}-${h.slice(12,16)}-${h.slice(16,20)}-${h.slice(20)}`;
}
```

---

## 0단계: 환경 점검

1. OS 감지: `uname -s` → Linux(WSL 포함) / Darwin(macOS)
   - WSL 판별: `uname -r`에 `microsoft` 또는 `WSL` 포함 여부
2. Node.js: `node --version` → v18 이상 필요. 없으면 설치 안내
3. yt-dlp: `yt-dlp --version` → 없으면 `pip install yt-dlp` 안내 (Python 필요)
4. OS 결과를 기억해둔다 → 8단계 스케줄링에서 사용

---

## 1단계: 프로젝트 폴더 생성

유저에게 프로젝트 경로를 묻는다. 이후 모든 파일은 이 경로(`{{PROJECT_DIR}}`) 기준.

```bash
mkdir -p {{PROJECT_DIR}} && cd {{PROJECT_DIR}}
```

**package.json** 생성:
```json
{
  "name": "youtube-scraper",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "dotenv": "^17.4.2"
  }
}
```

**.gitignore** 생성:
```
output/
node_modules/
.env
*.log
/tmp/
logs/
```

npm install 실행:
```bash
npm install
```

---

## 2단계: Notion Integration 생성

유저에게 다음을 안내한다:

> 1. https://www.notion.so/profile/integrations 에 접속하세요.
> 2. **"+ New Integration"** 을 클릭하세요.
> 3. 이름을 입력하세요 (예: "YouTube Scraper").
> 4. 워크스페이스를 선택하세요.
> 5. **"Submit"** 을 누르면 **Internal Integration Secret** (ntn_으로 시작)이 표시됩니다.
> 6. 이 토큰을 복사해서 알려주세요.

토큰을 입력받아 `.env` 파일에 저장:
```
NOTION_TOKEN=<입력받은 토큰>
```

---

## 3단계: Notion DB 설정

### 트레이드오프 안내 (반드시 유저에게 표로 보여준다)

| | A) 자동 생성 | B) 템플릿 복제 | C) 기존 DB 사용 |
|---|---|---|---|
| **편의성** | 가장 편함 — 원클릭 | 링크 복제 + Integration 수동 연결 | URL 입력 + 스키마 검증 |
| **뷰/필터** | 기본 테이블뷰만 | 커스텀 뷰·필터·정렬 포함 | 유저 설정 유지 |
| **프롬프트 템플릿** | 자동 생성 | 포함됨 | 없음 |
| **추천 대상** | 빠르게 시작하고 싶은 분 | 완성형 원하는 분 | DB가 이미 있는 분 |

### 분기 A: 자동 생성

1. `lib/notion.mjs`를 먼저 생성한다 → [부록: lib/notion.mjs] 참조
2. 유저에게 **"DB를 만들 상위 페이지 URL"** 을 입력받는다
3. URL에서 페이지 ID를 파싱한다 (위 `parseNotionId` 사용)
4. 아래 순서로 Notion 콘텐츠를 생성한다:

**순서가 중요하다**: `appendBlocks`와 자식 리소스 생성 순서가 곧 Notion UI 표시 순서다.
H3 → 스킬 페이지 → 토글(사용법) → 디바이더 → DB 순서로 생성해야 원하는 레이아웃이 나온다.

#### 4-1. H3 제목 추가

```javascript
await notion.appendBlocks(PARENT_PAGE_ID, [
  {
    type: 'heading_3',
    heading_3: {
      rich_text: [{ type: 'text', text: { content: '영상과 스크립트를 수집한 후 아래 스킬을 발동시키면 더욱 좋습니다 :)' } }],
      is_toggleable: false,
    }
  }
]);
```

#### 4-2. 스킬 프롬프트 페이지 생성

독립 페이지를 부모 페이지 하위에 생성 (DB 소속 아님 → `call()` 직접 사용).
H3 뒤에 자동 배치된다.

```javascript
const skillPage = await notion.call('POST', '/pages', {
  parent: { page_id: PARENT_PAGE_ID },
  properties: {
    title: { title: [{ text: { content: '[SKILL]_유튜브_콘텐츠_요약' } }] }
  }
});
await notion.updatePageMarkdown(skillPage.id, PROMPT_TEMPLATE);
```
→ `PROMPT_TEMPLATE` 내용은 [부록: 프롬프트 템플릿] 참조

#### 4-3. 토글(스킬 사용 방법) + 디바이더 추가

스킬 페이지 뒤에 배치된다.

```javascript
await notion.appendBlocks(PARENT_PAGE_ID, [
  {
    type: 'heading_4',
    heading_4: {
      rich_text: [{ type: 'text', text: { content: '스킬 사용 방법' } }],
      is_toggleable: true,
      children: [
        { type: 'paragraph', paragraph: { rich_text: [{ type: 'text', text: { content: '스킬 페이지에는 AI에게 전달할 작업 지침이 담겨 있습니다. 아래 두 가지 방법 중 편한 걸 사용하세요.' } }] } },
        { type: 'paragraph', paragraph: { rich_text: [{ type: 'text', text: { content: '방법 1 — 프롬프트 복사·붙여넣기' }, annotations: { bold: true } }] } },
        { type: 'numbered_list_item', numbered_list_item: { rich_text: [{ type: 'text', text: { content: '위 스킬 페이지를 열어 본문 전체를 복사합니다.' } }] } },
        { type: 'numbered_list_item', numbered_list_item: { rich_text: [{ type: 'text', text: { content: '유튜브 스크립트가 스크랩된 페이지를 엽니다.' } }] } },
        { type: 'numbered_list_item', numbered_list_item: { rich_text: [{ type: 'text', text: { content: '노션 AI 채팅창에 복사한 내용을 붙여넣고 전송합니다.' } }] } },
        { type: 'paragraph', paragraph: { rich_text: [{ type: 'text', text: { content: '방법 2 — @ 멘션으로 스킬 페이지 첨부' }, annotations: { bold: true } }] } },
        { type: 'numbered_list_item', numbered_list_item: { rich_text: [{ type: 'text', text: { content: '유튜브 스크립트가 스크랩된 페이지를 엽니다.' } }] } },
        { type: 'numbered_list_item', numbered_list_item: { rich_text: [{ type: 'text', text: { content: '노션 AI 채팅창에 @를 입력해 위 스킬 페이지를 멘션합니다.' } }] } },
        { type: 'numbered_list_item', numbered_list_item: { rich_text: [{ type: 'text', text: { content: '"이 지침대로 작업해줘" 라고 입력하고 전송합니다.' } }] } },
      ]
    }
  },
  { type: 'divider', divider: {} }
]);
```

#### 4-4. DB 생성

디바이더 뒤에 자동 배치된다.

```javascript
const db = await notion.createDatabase(PARENT_PAGE_ID, 'YouTube 요약', '🎬', DB_SCHEMA);
```

→ `DB_SCHEMA` 내용은 [부록: DB 스키마] 참조

DB ID를 `.env`에 추가:
```
NOTION_DB_ID=<생성된 DB ID>
```

**안내**: "기본 테이블뷰만 생성됩니다. 갤러리뷰, 정렬, 필터 등은 Notion에서 직접 설정하세요."

### 분기 B: 템플릿 복제

유저에게 안내:

> 아래 링크에서 템플릿을 복제하세요:
> https://ioooss.notion.site/Youtube-148dd1dcd64483ab89ba0199271a43b4
>
> 1. 링크를 열고 우측 상단 **"Duplicate"** 을 클릭하세요.
> 2. 복제된 페이지에서 **"..."** → **"Connections"** → 2단계에서 만든 Integration을 추가하세요.
> 3. 복제된 DB의 URL을 알려주세요.

URL을 입력받아 DB ID를 파싱하고 `.env`에 추가:
```
NOTION_DB_ID=<파싱한 DB ID>
```

### 분기 C: 기존 DB 사용

1. 유저에게 DB URL을 입력받아 ID를 파싱한다
2. Integration 연결을 안내한다:
   > DB 페이지에서 **"..."** → **"Connections"** → 2단계에서 만든 Integration을 추가하세요.
3. `lib/notion.mjs`가 아직 없으면 생성한다
4. DB 스키마를 검증한다:

```javascript
const db = await notion.call('GET', `/databases/${DB_ID}`);
const dsId = db.data_sources?.[0]?.id;
const ds = await notion.call('GET', `/data_sources/${dsId}`);
console.log(JSON.stringify(ds.properties, null, 2));
```

5. 필수 속성 존재 여부를 확인한다:
   - `제목` (title) — 필수
   - `영상ID` (rich_text) — 필수
   - `채널` (select) — 필수
   - `URL` (url) — 필수
   - `게시일` (date) — 필수
   - `by AI` (checkbox) — 필수
   - 나머지 (조회수, 좋아요, 요약, 태그) — 선택

6. 누락 속성이 있으면 유저와 협의하여 추가 여부를 결정한다
7. 속성명이 다르면 유저에게 확인 후 `scrape.mjs`의 속성명을 수정한다

`.env`에 추가:
```
NOTION_DB_ID=<파싱한 DB ID>
```

---

## 4단계: 채널 등록

유저에게 묻는다: **"구독할 유튜브 채널 URL을 입력하세요. 여러 개면 줄바꿈으로 구분해주세요."**

채널 URL 형식 파싱:
- `https://www.youtube.com/channel/UC...` → ID는 `UC...` 부분
- `https://www.youtube.com/@handle` → 페이지에서 channel ID 추출 필요
- 직접 ID 입력 (UC로 시작) → 그대로 사용

`@handle` 형식인 경우 채널 페이지 소스에서 ID를 추출:
```bash
curl -s "https://www.youtube.com/@handle" | grep -oP '"channelId":"(UC[^"]+)"' | head -1
```

`channels.json` 생성:
```json
[
  { "id": "UC...", "name": "채널이름" }
]
```

채널 이름은 유저에게 확인하거나, 유튜브 페이지에서 추출한다.

---

## 5단계: Slack 알림 (선택)

유저에게 묻는다: **"스크랩 에러 발생 시 Slack 알림을 받으시겠습니까?"**

### 사용함

안내:
> 1. https://api.slack.com/apps 에서 **"Create New App"** → **"From scratch"**
> 2. 앱 이름 입력 (예: "YouTube Scraper")
> 3. **OAuth & Permissions** → **Bot Token Scopes** → `chat:write` 추가
> 4. **Install to Workspace** → 봇 토큰 복사 (xoxb-로 시작)
> 5. 알림 받을 채널에 봇을 초대: `/invite @봇이름`

토큰을 `.env`에 추가:
```
SLACK_BOT_TOKEN=<입력받은 토큰>
```

**`scrape.mjs` 생성 시 Slack 코드를 포함한다.**

### 사용 안 함

**`scrape.mjs` 생성 시 아래 Slack 관련 코드를 모두 제거한다:**
- `sendSlackAlert` 함수 전체
- 모든 `sendSlackAlert(...)` 호출문 (await 포함)
- `await sendSlackAlert(...)` 호출 시 `.catch(() => {})` 포함 전체 라인 삭제
- `.env.example`에서 `SLACK_BOT_TOKEN` 라인 제거

---

## 6단계: 코드 생성

아래 파일들을 생성한다. 코드 내용은 [부록: 코드 템플릿] 참조.

1. `lib/notion.mjs` — 3단계에서 이미 생성했으면 스킵
2. `scrape.mjs` — 5단계 결과에 따라 Slack 코드 포함/제거
3. `.env.example` — Slack 여부에 따라 내용 조정
4. `run.sh` — `{{PROJECT_DIR}}`를 실제 경로로 치환

---

## 7단계: 테스트 실행

```bash
cd {{PROJECT_DIR}} && node scrape.mjs --days 7
```

확인사항:
- RSS 피드 정상 수신 여부
- Notion DB에 데이터 저장 여부
- `output/` 폴더에 로컬 MD 생성 여부
- 에러 발생 시 원인 파악 및 수정

테스트 성공 시 유저에게 보고한다.

---

## 8단계: 스케줄링 (OS 네이티브)

0단계에서 감지한 OS에 따라 분기한다.

### Windows (WSL)

1. `register-task.ps1` 생성 → [부록: register-task.ps1] 참조
   - `{{PROJECT_DIR}}`를 실제 WSL 경로로 치환
   - `{{WIN_PROJECT_DIR}}`를 Windows 경로로 치환 (예: `/mnt/c/dev/my-scraper` → `C:\dev\my-scraper`)
2. 실행 시간을 유저에게 확인 (기본: 매일 08:50)
3. 등록 안내:
   > PowerShell을 **관리자 권한**으로 열고 다음을 실행하세요:
   > ```
   > powershell -ExecutionPolicy Bypass -File {{WIN_PROJECT_DIR}}\register-task.ps1
   > ```

### macOS

1. `com.youtube-scraper.plist` 생성 → [부록: launchd plist] 참조
   - `{{PROJECT_DIR}}`를 실제 경로로 치환
2. 실행 시간을 유저에게 확인 (기본: 매일 08:50)
3. 등록 안내:
   > ```bash
   > cp {{PROJECT_DIR}}/com.youtube-scraper.plist ~/Library/LaunchAgents/
   > launchctl load ~/Library/LaunchAgents/com.youtube-scraper.plist
   > ```

### Linux (네이티브)

crontab 등록 안내:
```bash
crontab -e
# 아래 줄 추가 (매일 08:50):
50 8 * * * cd {{PROJECT_DIR}} && bash run.sh
```

---

## 완료

유저에게 최종 보고:
- 생성된 파일 목록
- Notion DB 링크
- 스케줄 설정 내용
- 수동 실행 방법: `cd {{PROJECT_DIR}} && node scrape.mjs --days 7`

---
---

# 부록: 코드 템플릿

## lib/notion.mjs

```javascript
/**
 * Minimal Notion API helper for youtube-scraper
 *
 * NOTION_TOKEN 환경변수 필수 (.env 또는 시스템 환경변수)
 * API Version: 2026-03-11 (DB ID → DS ID 자동 변환)
 */

const API_VERSION = '2026-03-11';
const BASE = 'https://api.notion.com/v1';

const TOKEN = process.env.NOTION_TOKEN;
if (!TOKEN) throw new Error('NOTION_TOKEN 환경변수가 설정되지 않았습니다. .env 파일을 확인하세요.');

// ── Core HTTP ────────────────────────────────────────────
async function call(method, path, body) {
  const url = path.startsWith('http') ? path : `${BASE}${path}`;
  const res = await fetch(url, {
    method,
    headers: {
      Authorization: `Bearer ${TOKEN}`,
      'Notion-Version': API_VERSION,
      'Content-Type': 'application/json',
    },
    body: body != null ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const e = new Error(err.message || `Notion API ${res.status}`);
    e.status = res.status;
    throw e;
  }
  return res.json();
}

// ── Retry on 429 ─────────────────────────────────────────
async function withRetry(fn, maxRetries = 2) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (err.status === 429 && attempt < maxRetries) {
        await new Promise(r => setTimeout(r, 1000));
        continue;
      }
      throw err;
    }
  }
}

// ── DB ID → DS ID 변환 (2026-03-11 필수) ─────────────────
const _dsCache = new Map();

async function resolveDataSourceId(dbId) {
  if (_dsCache.has(dbId)) return _dsCache.get(dbId);
  const db = await call('GET', `/databases/${dbId}`);
  const dsId = db.data_sources?.[0]?.id;
  if (!dsId) throw new Error(`data_source ID not found for database ${dbId}`);
  _dsCache.set(dbId, dsId);
  return dsId;
}

// ── Database ─────────────────────────────────────────────
async function queryDatabase(dbId, { filter, sorts, pageSize = 100, startCursor } = {}) {
  const dsId = await resolveDataSourceId(dbId);
  const body = { page_size: pageSize };
  if (filter) body.filter = filter;
  if (sorts) body.sorts = sorts;
  if (startCursor) body.start_cursor = startCursor;
  return call('POST', `/data_sources/${dsId}/query`, body);
}

async function queryAll(dbId, opts = {}) {
  const pages = [];
  let cursor;
  do {
    const res = await queryDatabase(dbId, { ...opts, startCursor: cursor });
    pages.push(...res.results);
    cursor = res.has_more ? res.next_cursor : null;
  } while (cursor);
  return pages;
}

async function createDatabase(parentPageId, title, emoji, properties) {
  // API 2026-03-11: POST /databases의 properties 파라미터가 무시됨
  // DB 생성 → data_source ID 추출 → PATCH /data_sources/{dsId}로 properties 추가
  const db = await call('POST', '/databases', {
    parent: { type: 'page_id', page_id: parentPageId },
    icon: emoji ? { type: 'emoji', emoji } : undefined,
    title: [{ type: 'text', text: { content: title } }],
  });

  const dsId = db.data_sources?.[0]?.id;
  if (!dsId) throw new Error('createDatabase: data_source ID를 추출할 수 없음');

  if (properties && Object.keys(properties).length > 0) {
    const patchProps = {};
    for (const [name, schema] of Object.entries(properties)) {
      if (schema.title !== undefined) {
        patchProps['Name'] = { name };
      } else {
        patchProps[name] = schema;
      }
    }
    const ds = await call('PATCH', `/data_sources/${dsId}`, { properties: patchProps });
    return { ...db, properties: ds.properties, data_source_id: dsId };
  }

  return db;
}

// ── Pages ─────────────────────────────────────────────────
async function createPage(dbId, properties, cover) {
  const body = { parent: { database_id: dbId }, properties };
  if (cover) body.cover = cover;
  try {
    return await call('POST', '/pages', body);
  } catch (err) {
    if (err.status === 404) {
      body.parent = { data_source_id: dbId };
      return call('POST', '/pages', body);
    }
    throw err;
  }
}

async function updatePage(pageId, patch) {
  return call('PATCH', `/pages/${pageId}`, patch);
}

// ── Markdown ─────────────────────────────────────────────
async function getPageMarkdown(pageId) {
  const res = await call('GET', `/pages/${pageId}/markdown`);
  return res.markdown ?? res;
}

async function updatePageMarkdown(pageId, markdown) {
  return call('PATCH', `/pages/${pageId}/markdown`, {
    type: 'replace_content',
    replace_content: { new_str: markdown },
  });
}

// ── Blocks ────────────────────────────────────────────────
async function appendBlocks(blockId, children) {
  return call('PATCH', `/blocks/${blockId}/children`, { children });
}

// ── Bulk upsert ───────────────────────────────────────────
function extractValue(page, propName) {
  const p = page.properties?.[propName];
  if (!p) return undefined;
  switch (p.type) {
    case 'title': return p.title?.[0]?.plain_text;
    case 'rich_text': return p.rich_text?.[0]?.plain_text;
    case 'number': return p.number;
    case 'select': return p.select?.name;
    case 'url': return p.url;
    default: return undefined;
  }
}

async function bulkUpsert(dbId, matchKey, items, { concurrency = 15, onProgress } = {}) {
  const allPages = await queryAll(dbId);
  const cache = new Map();
  for (const p of allPages) {
    const val = extractValue(p, matchKey);
    if (val != null) cache.set(String(val), p.id);
  }

  const stats = { created: 0, updated: 0, failed: 0, errors: [] };
  for (let i = 0; i < items.length; i += concurrency) {
    const chunk = items.slice(i, i + concurrency);
    const settled = await Promise.allSettled(
      chunk.map(item =>
        withRetry(async () => {
          const existingId = cache.get(String(item.matchValue));
          if (existingId) {
            await updatePage(existingId, { properties: item.properties });
            return 'updated';
          } else {
            const page = await createPage(dbId, item.properties, item.cover);
            cache.set(String(item.matchValue), page.id);
            return 'created';
          }
        })
      )
    );
    for (const s of settled) {
      if (s.status === 'fulfilled') stats[s.value]++;
      else { stats.failed++; stats.errors.push(s.reason?.message); }
    }
    if (onProgress) onProgress(Math.min(i + concurrency, items.length), items.length);
  }
  return stats;
}

// ── Property builders ─────────────────────────────────────
const prop = {
  title: (text) => ({ title: [{ text: { content: text } }] }),
  richText: (text) => ({ rich_text: [{ text: { content: text } }] }),
  select: (name) => ({ select: { name } }),
  url: (url) => ({ url }),
  date: (start, end) => ({ date: end ? { start, end } : { start } }),
  checkbox: (checked) => ({ checkbox: checked }),
  number: (n) => ({ number: n }),
};

// ── Block builders ────────────────────────────────────────
const block = {
  divider: () => ({ object: 'block', type: 'divider', divider: {} }),
};

export const notion = {
  call,
  queryAll,
  queryDatabase,
  createDatabase,
  createPage,
  updatePage,
  getPageMarkdown,
  updatePageMarkdown,
  appendBlocks,
  bulkUpsert,
  prop,
  block,
};
```

---

## scrape.mjs

Slack을 사용하지 않는 경우: `// [SLACK]` 주석이 달린 줄과 `sendSlackAlert` 함수 전체를 제거한다.

```javascript
#!/usr/bin/env node
/**
 * YouTube Channel RSS Scraper
 *
 * Usage:
 *   node scrape.mjs                   # 최근 7일, 모든 채널
 *   node scrape.mjs --days 14         # 최근 14일
 *   node scrape.mjs --channel UC...   # 특정 채널만
 *   node scrape.mjs --no-notion       # 로컬 MD만 저장
 */

import 'dotenv/config';
import { execSync } from 'child_process';
import { existsSync, mkdirSync, writeFileSync, readFileSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// ── CLI 인자 파싱 ──────────────────────────────────────────
const args = process.argv.slice(2);
const getArg = (flag) => { const i = args.indexOf(flag); return i !== -1 ? args[i + 1] : null; };
const hasFlag = (flag) => args.includes(flag);

const DAYS = parseInt(getArg('--days') || '7', 10);
const FILTER_CHANNEL = getArg('--channel');
const NO_NOTION = hasFlag('--no-notion');
const DB_ID = getArg('--db-id') || process.env.NOTION_DB_ID || null;

// ── 채널 목록 로드 ─────────────────────────────────────────
const channelsPath = join(__dirname, 'channels.json');
let channels = JSON.parse(readFileSync(channelsPath, 'utf-8'));
if (FILTER_CHANNEL) {
  channels = channels.filter((c) => c.id === FILTER_CHANNEL);
  if (channels.length === 0) { console.error(`채널 ID를 찾을 수 없습니다: ${FILTER_CHANNEL}`); process.exit(1); }
}

// ── Notion 설정 ────────────────────────────────────────────
let notion = null;
if (!NO_NOTION) {
  try {
    const { notion: n } = await import('./lib/notion.mjs');
    notion = n;
  } catch (e) {
    console.warn('⚠️  Notion 모듈 로드 실패 — --no-notion 모드로 전환합니다.');
    console.warn(e.message);
    await sendSlackAlert(`Notion 모듈 로드 실패\n\`${e.message}\``).catch(() => {}); // [SLACK]
  }
}

// ── 유틸 ──────────────────────────────────────────────────
function run(cmd) {
  try { return execSync(cmd, { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'] }).trim(); }
  catch { return null; }
}

function parseRSS(xml) {
  const entries = [];
  const entryRegex = /<entry>([\s\S]*?)<\/entry>/g;
  let match;
  while ((match = entryRegex.exec(xml)) !== null) {
    const block = match[1];
    const get = (tag) => { const m = block.match(new RegExp(`<${tag}[^>]*>([\\s\\S]*?)<\\/${tag}>`)); return m ? m[1].trim() : ''; };
    const videoId = get('yt:videoId');
    if (!videoId) continue;
    entries.push({ videoId, title: get('title'), published: get('published'), link: `https://www.youtube.com/watch?v=${videoId}` });
  }
  return entries;
}

function isoDate(str) { return new Date(str).toISOString().slice(0, 10); }
function cutoffDate() { const d = new Date(); d.setDate(d.getDate() - DAYS); return d; }
function today() { return new Date().toISOString().slice(0, 10); }
function ensureDir(dir) { if (!existsSync(dir)) mkdirSync(dir, { recursive: true }); }

// ── Slack 에러 알림 ──────────────────────────────────── [SLACK]
async function sendSlackAlert(message) {                          // [SLACK]
  try {                                                           // [SLACK]
    const token = process.env.SLACK_BOT_TOKEN;                    // [SLACK]
    if (!token) { console.warn('  Slack 토큰 없음 — 알림 스킵'); return; } // [SLACK]
    const res = await fetch('https://slack.com/api/chat.postMessage', { // [SLACK]
      method: 'POST',                                             // [SLACK]
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' }, // [SLACK]
      body: JSON.stringify({ channel: '#자동화메시지', text: `🚨 *youtube-scrap 에러*\n${message}` }), // [SLACK]
    });                                                           // [SLACK]
    const data = await res.json();                                // [SLACK]
    if (!data.ok) console.warn('  Slack 알림 실패:', data.error); // [SLACK]
  } catch (e) { console.warn('  Slack 알림 전송 중 오류:', e.message); } // [SLACK]
}                                                                 // [SLACK]

// 2000자 단위로 분할 (Notion rich_text 제한)
function chunkText(text, size = 1900) {
  const chunks = [];
  for (let i = 0; i < text.length; i += size) chunks.push(text.slice(i, i + size));
  return chunks;
}

async function buildNotionPage(pageId, video) {
  await notion.updatePageMarkdown(pageId, '');

  const transcriptChunks = video.transcript
    ? chunkText(video.transcript).map(chunk => ({
        type: 'paragraph',
        paragraph: { rich_text: [{ type: 'text', text: { content: chunk } }] },
      }))
    : [{ type: 'paragraph', paragraph: { rich_text: [{ type: 'text', text: { content: '(자막 없음)' } }] } }];

  await notion.appendBlocks(pageId, [
    { type: 'video', video: { type: 'external', external: { url: video.url } } },
    {
      type: 'heading_2',
      heading_2: {
        rich_text: [{ type: 'text', text: { content: '스크립트 전문' } }],
        is_toggleable: true,
        children: [
          {
            type: 'callout',
            callout: {
              rich_text: [{ type: 'text', text: { content: '스크립트 전문' }, annotations: { bold: true } }],
              icon: { type: 'emoji', emoji: '💡' },
              color: 'default',
              children: [
                { type: 'divider', divider: {} },
                ...transcriptChunks,
              ],
            },
          },
        ],
      },
    },
  ]);
}

// ── Notion DB에서 기존 영상 ID 목록 조회 ──────────────────
async function fetchExistingIds(dbId) {
  if (!notion || !dbId) return new Set();
  try {
    const pages = await notion.queryAll(dbId);
    return new Set(pages.map((p) => p.properties?.제목?.title?.[0]?.plain_text).filter(Boolean));
  } catch (e) {
    console.warn('⚠️  Notion 기존 영상 조회 실패:', e.message);
    return new Set();
  }
}

// ── Notion upsert ──────────────────────────────────────────
async function upsertToNotion(dbId, videos) {
  if (!notion || !dbId || videos.length === 0) return { created: 0, updated: 0 };
  const items = videos.map((v) => ({
    matchValue: v.title,
    properties: {
      '제목': notion.prop.title(v.title),
      '영상ID': notion.prop.richText(v.videoId),
      '채널': notion.prop.select(v.channel),
      'URL': notion.prop.url(v.url),
      '게시일': notion.prop.date(v.publishDate),
    },
    cover: { type: 'external', external: { url: `https://img.youtube.com/vi/${v.videoId}/maxresdefault.jpg` } },
  }));

  const stats = await notion.bulkUpsert(dbId, '제목', items, {
    onProgress: (done, total) => process.stdout.write(`\r  Notion upsert: ${done}/${total}`),
  });
  process.stdout.write('\n');

  for (const v of videos) {
    try {
      const pages = await notion.queryAll(dbId, { filter: { property: '제목', title: { equals: v.title } } });
      if (pages.length > 0) await buildNotionPage(pages[0].id, v);
    } catch (e) {
      console.warn(`  ⚠️  ${v.videoId} 본문 업데이트 실패:`, e.message);
      await sendSlackAlert(`Notion 본문 업데이트 실패: ${v.videoId}\n\`${e.message}\``); // [SLACK]
    }
  }
  return stats;
}

// ── 전역 unhandled 에러 ────────────────────────────────────
process.on('unhandledRejection', async (reason) => {
  const msg = reason instanceof Error ? reason.message : String(reason);
  console.error('unhandledRejection:', msg);
  await sendSlackAlert(`예기치 않은 에러 발생\n\`${msg}\``); // [SLACK]
  process.exit(1);
});

// ── 메인 ──────────────────────────────────────────────────
const cutoff = cutoffDate();
const outputBase = join(__dirname, 'output', today());
ensureDir(outputBase);

const allResults = [];
const statsTotal = { channels: 0, rss: 0, dateFiltered: 0, existing: 0, processed: 0 };

for (const channel of channels) {
  console.log(`\n[채널] ${channel.name} (${channel.id})`);
  statsTotal.channels++;

  const xml = run(`curl -s "https://www.youtube.com/feeds/videos.xml?channel_id=${channel.id}"`);
  if (!xml || xml.includes('<error>')) {
    console.log('  ⚠️  RSS 피드 없음 — 스킵');
    await sendSlackAlert(`RSS 피드 없음: ${channel.name} (${channel.id})`); // [SLACK]
    continue;
  }
  const entries = parseRSS(xml);
  console.log(`  RSS: ${entries.length}개 항목`);
  statsTotal.rss += entries.length;

  const recent = entries.filter((e) => new Date(e.published) >= cutoff);
  const skippedDate = entries.length - recent.length;
  statsTotal.dateFiltered += skippedDate;
  console.log(`  날짜 필터(최근 ${DAYS}일): ${recent.length}개 통과, ${skippedDate}개 제외`);
  if (recent.length === 0) continue;

  const existingIds = await fetchExistingIds(DB_ID);
  const newVideos = recent.filter((v) => !existingIds.has(v.title)).map((v) => ({ ...v, channel: channel.name }));
  const skippedExisting = recent.length - newVideos.length;
  statsTotal.existing += skippedExisting;
  console.log(`  Notion 대조: ${newVideos.length}개 신규, ${skippedExisting}개 기존 스킵`);
  if (newVideos.length === 0) continue;

  for (const v of newVideos) {
    console.log(`  처리: ${v.videoId} — ${v.title}`);

    let transcript = null;
    const tmpFile = `/tmp/yt_${v.videoId}`;
    let ytdlpOut = '';
    try {
      ytdlpOut = execSync(
        `yt-dlp --js-runtimes node --write-sub --write-auto-sub --skip-download --sub-lang ko --sub-format json3 -o "${tmpFile}" "${v.link}"`,
        { encoding: 'utf-8', stdio: ['pipe', 'pipe', 'pipe'] }
      ).trim();
    } catch (e) { ytdlpOut = `[exit ${e.status}] ${(e.stdout || '')}${(e.stderr || '')}`; }
    console.log(`    yt-dlp: ${ytdlpOut.slice(0, 500) || '(출력 없음)'}`);

    try {
      const subFiles = readdirSync('/tmp').filter(f => f.startsWith(`yt_${v.videoId}`) && f.endsWith('.json3'));
      console.log(`    자막 파일: ${subFiles.length > 0 ? subFiles.join(', ') : '없음'}`);
      if (subFiles.length > 0) {
        const data = JSON.parse(readFileSync(`/tmp/${subFiles[0]}`, 'utf-8'));
        transcript = data.events
          .filter(e => e.segs)
          .map(e => e.segs.map(s => s.utf8).join(''))
          .join(' ').replace(/\n/g, ' ').replace(/\s+/g, ' ').trim() || null;
        subFiles.forEach(f => run(`rm -f "/tmp/${f}"`));
      }
    } catch (e) {
      console.warn(`    ⚠️  자막 추출 실패 (${v.videoId}):`, e.message);
      await sendSlackAlert(`자막 추출 실패: [${v.title}](${v.link})\n\`${e.message}\``); // [SLACK]
    }

    const video = { ...v, publishDate: isoDate(v.published), url: v.link, transcript };
    const mdLines = [
      `# ${video.title}`, '', `| 채널 | ${video.channel} |`, `|------|------|`,
      `| 게시일 | ${video.publishDate} |`, `| URL | ${video.url} |`, '', `## 자막 전문`, '',
      video.transcript || '_(자막 없음)_',
    ];
    const mdPath = join(outputBase, `${v.videoId}.md`);
    writeFileSync(mdPath, mdLines.join('\n'), 'utf-8');
    console.log(`    ✓ 저장: output/${today()}/${v.videoId}.md`);

    allResults.push(video);
    statsTotal.processed++;
  }
}

if (allResults.length > 0) {
  const indexLines = [
    `# YouTube 스크랩 — ${today()}`, '',
    `> 기간: 최근 ${DAYS}일 | 채널: ${statsTotal.channels}개 | 신규 영상: ${allResults.length}개`, '',
    `| 채널 | 제목 | 게시일 | 링크 |`, `|------|------|--------|------|`,
    ...allResults.map((v) => `| ${v.channel} | ${v.title} | ${v.publishDate} | [▶](${v.url}) |`),
  ];
  writeFileSync(join(outputBase, 'index.md'), indexLines.join('\n'), 'utf-8');
  console.log(`\n✓ index.md 생성: output/${today()}/index.md`);
}

if (!NO_NOTION && DB_ID && allResults.length > 0) {
  console.log(`\nNotion DB 업서트 중... (DB ID: ${DB_ID})`);
  const stats = await upsertToNotion(DB_ID, allResults);
  console.log(`✓ Notion: ${stats.created}개 생성, ${stats.updated}개 업데이트`);
} else if (!NO_NOTION && !DB_ID && allResults.length > 0) {
  console.log(`\n💡 Notion 업서트를 하려면 --db-id <notion-db-id> 를 지정하세요.`);
}

console.log(`
══════════════════════════════════
  완료 리포트
══════════════════════════════════
  채널: ${statsTotal.channels}개
  RSS 항목: ${statsTotal.rss}개
  날짜 필터 제외: ${statsTotal.dateFiltered}개
  기존 영상 스킵: ${statsTotal.existing}개
  신규 처리: ${statsTotal.processed}개
══════════════════════════════════`);
```

---

## .env.example

Slack 사용 시:
```
NOTION_TOKEN=ntn_xxxxxxxxxxxxxxxxxxxxx
NOTION_DB_ID=your-notion-database-id
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
```

Slack 미사용 시:
```
NOTION_TOKEN=ntn_xxxxxxxxxxxxxxxxxxxxx
NOTION_DB_ID=your-notion-database-id
```

---

## run.sh

`{{PROJECT_DIR}}`를 실제 프로젝트 경로로 치환한다.

```bash
#!/bin/bash
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

LOG_DIR="{{PROJECT_DIR}}/logs"
LOG_FILE="$LOG_DIR/scrape_$(date +%Y%m%d).log"
mkdir -p "$LOG_DIR"

echo "=== 시작: $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG_FILE"
cd {{PROJECT_DIR}}
node scrape.mjs >> "$LOG_FILE" 2>&1
EXIT_CODE=$?
echo "=== 완료: $(date '+%Y-%m-%d %H:%M:%S') (exit: $EXIT_CODE) ===" >> "$LOG_FILE"

exit $EXIT_CODE
```

생성 후 실행 권한 부여: `chmod +x run.sh`

---

## register-task.ps1 (Windows)

`{{PROJECT_DIR}}`를 WSL 경로로, `{{TASK_TIME}}`을 실행 시간으로 치환한다.

```powershell
$taskName = "YouTubeScraper"

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$action   = New-ScheduledTaskAction -Execute "C:\Windows\System32\wsl.exe" -Argument "bash {{PROJECT_DIR}}/run.sh"
$trigger  = New-ScheduledTaskTrigger -Daily -At "{{TASK_TIME}}"
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "YouTube RSS 스크래퍼 — 매일 자동 실행" `
    -Force

Write-Host "등록 완료 (StartWhenAvailable 활성화)"
```

---

## com.youtube-scraper.plist (macOS)

`{{PROJECT_DIR}}`를 실제 경로로, 시간을 유저 요청에 맞게 치환한다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.youtube-scraper</string>
    <key>ProgramArguments</key>
    <array>
        <string>bash</string>
        <string>{{PROJECT_DIR}}/run.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>50</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{{PROJECT_DIR}}/logs/launchd.log</string>
    <key>StandardErrorPath</key>
    <string>{{PROJECT_DIR}}/logs/launchd-error.log</string>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

---
---

# 부록: Notion 콘텐츠

## DB 스키마

3단계 분기 A에서 `createDatabase`에 전달할 properties 객체:

```javascript
const DB_SCHEMA = {
  '제목': { title: {} },
  '영상ID': { rich_text: {} },
  '채널': { select: {} },
  'URL': { url: {} },
  '게시일': { date: {} },
  '조회수': { number: { format: 'number_with_commas' } },
  '좋아요': { number: { format: 'number_with_commas' } },
  '요약': { rich_text: {} },
  '태그': { multi_select: {
    options: [
      { name: 'AI', color: 'purple' },
      { name: '개발', color: 'blue' },
      { name: '비즈니스', color: 'yellow' },
      { name: '마케팅', color: 'pink' },
      { name: '생산성', color: 'green' },
      { name: '교육', color: 'orange' },
    ],
  } },
  '보정 및 요약': { checkbox: {} },
};
```

---

## 프롬프트 템플릿

3단계 분기 A에서 스킬 프롬프트 페이지에 `updatePageMarkdown`으로 작성할 내용:

````markdown
## 트리거 조건

YouTube 요약 DB 페이지의 스크립트에 대해 **오탈자 보정, 요약, 인사이트 도출** 작업을 요청받았을 때 발동한다.

- 시동어 예시: "요약해줘", "보정하고 요약해", "인사이트 뽑아줘", 또는 DB 페이지를 가리키며 작업을 지시하는 경우

## 실행 지시

### 0단계: 맥락 수집 (하드코딩 금지)

- 대상 페이지를 열어 **영상 제목, 채널명, 스크립트 전문**을 확인한다.
- 이 세 가지가 이후 모든 판단(오탈자 식별, 요약 분할, 인사이트 방향)의 맥락 기반이 된다.
- 영상의 분야(역사, IT, 교육 등)를 스크립트 내용에서 추론하여 이후 단계에 적용한다.

### 1단계: 오탈자 보정

- 음성 인식(STT) 특유의 오류 패턴을 맥락 기반으로 식별하고 보정한다.

#### 보정 대상 유형

- **고유명사 오변환**: 인물명, 지명, 사건명, 기술 용어 등 (분야에 따라 달라짐)
- **일반 어휘 오탈자**: 음절 탈락, 동음이의 오변환, 띄어쓰기 누락
- **숫자 오류**: 명백한 자릿수 누락 등 (확신할 수 없는 숫자는 보류)

#### 보정 불가 판단 기준

- 문맥만으로 원래 값을 특정할 수 없는 경우(숫자 누락 등)는 보류하고 보고

### 2단계: 스크립트 요약

- 1단계에서 보정된 스크립트를 기반으로 요약본을 작성한다.

#### 덩어리 분할 기준

- 스크립트 내 **화제 전환 지점**(시간·장소·논점·주체 전환)을 감지하여 단락으로 나눔
- 덩어리 수는 콘텐츠 밀도에 맞게 자율 판단 (하드코딩 금지)

#### 요약 방식

- 각 덩어리마다 **핵심 주장 + 뒷받침 근거**를 개조식으로 정리
- 고유명사·숫자·연도 등 팩트는 보존
- 화자의 해석/관점도 구분하여 포함
- 단순 반복·접속 표현·구어체 군더더기는 제거

### 3단계: 페이지 삽입

기존 "스크립트" 토글 아래에 토글 헤딩 블록을 삽입한다.

#### 출력 블록 구조 (고정)

```markdown
## 스크립트 요약 {toggle="true"}
	<callout icon="📌">
		### 스크립트 요약
		---
		#### 소제목
		- 불렛 내용
	</callout>
```

#### 규칙

- 토글: `## 제목 {toggle="true"}` (토글 헤딩 H2)
- 콜아웃 내부: `### 콜아웃 타이틀` → `---` 구분선 → `####` 소제목 → 불렛

### 4단계: 속성 업데이트

- 작업 완료 후 해당 페이지의 `보정 및 요약` 체크박스를 `true`로 변경

## 주의 사항/한계

<callout icon="⚠️" color="red_bg">
	- 오탈자 보정 시 화자의 의도적 표현(사투리, 조어 등)을 오탈자로 오인하지 않도록 주의
	- 숫자·고유명사 중 맥락만으로 특정 불가한 항목은 보정하지 않고 보고
	- 요약·발문의 개수를 하드코딩하지 않음 — 콘텐츠 밀도에 따라 자율 판단
	- 스크립트가 없는 페이지에는 이 스킬을 적용하지 않음
</callout>
````
