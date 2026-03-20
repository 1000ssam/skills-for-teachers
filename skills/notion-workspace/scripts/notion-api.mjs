/**
 * Notion API 공용 모듈
 *
 * 설정: 이 스킬 디렉토리의 config.json에 Notion Integration Token을 저장.
 *       { "token": "ntn_..." }
 */

import { readFileSync, statSync } from 'fs';
import { basename, extname, dirname, join } from 'path';
import { fileURLToPath } from 'url';

// ── 크리덴셜 자동 로드 (config.json) ────────────────────
const __dirname = dirname(fileURLToPath(import.meta.url));
const CONFIG_PATH = join(__dirname, '..', 'config.json');

function loadToken() {
  try {
    const config = JSON.parse(readFileSync(CONFIG_PATH, 'utf-8'));
    if (!config.token?.startsWith('ntn_')) {
      throw new Error('config.json의 token이 유효하지 않습니다. "ntn_"으로 시작하는 값을 설정하세요.');
    }
    return config.token;
  } catch (e) {
    if (e.code === 'ENOENT') {
      throw new Error(
        'config.json이 없습니다. notion-workspace 스킬 폴더에 config.json을 생성하고 ' +
        '{ "token": "ntn_..." } 형식으로 Notion Integration Token을 설정하세요.'
      );
    }
    throw e;
  }
}

const TOKEN = loadToken();

// ── API 버전 ─────────────────────────────────────────────
const API_VERSION = '2026-03-11';
// ── Base fetch ───────────────────────────────────────────
const BASE = 'https://api.notion.com/v1';

async function call(method, path, body, { raw = false } = {}) {
  const url = path.startsWith('http') ? path : `${BASE}${path}`;
  const res = await fetch(url, {
    method,
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Notion-Version': API_VERSION,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if (!res.ok) {
    const err = new Error(`Notion API ${res.status}: ${data.message}`);
    err.status = res.status;
    err.code = data.code;
    err.response = data;
    throw err;
  }
  return raw ? { data, headers: res.headers } : data;
}

// ── 검색 ─────────────────────────────────────────────────
async function search(query, { filter, pageSize = 10 } = {}) {
  const body = { query, page_size: pageSize };
  if (filter) {
    // 2026-03-11: 'database' → 'data_source'
    const value = filter === 'database' ? 'data_source' : filter;
    body.filter = { property: 'object', value };
  }
  return call('POST', '/search', body);
}

// ── 데이터베이스 ─────────────────────────────────────────
async function createDatabase(parentPageId, title, emoji, properties) {
  return call('POST', '/databases', {
    parent: { type: 'page_id', page_id: parentPageId },
    icon: emoji ? { type: 'emoji', emoji } : undefined,
    title: [{ type: 'text', text: { content: title } }],
    properties,
  });
}

/**
 * DB 조회: DB ID → /databases/ 로 메타데이터 + DS ID 추출,
 * 이어서 /data_sources/ 로 properties 포함 전체 정보 반환.
 * DS ID를 직접 넘기면 /data_sources/ 만 호출.
 */
async function getDatabase(dbId) {
  // 먼저 /databases/ 시도하여 data_sources 추출
  const db = await call('GET', `/databases/${dbId}`).catch(() => null);
  if (db?.data_sources?.[0]?.id) {
    const dsId = db.data_sources[0].id;
    _dsCache.set(dbId, dsId);
    const ds = await call('GET', `/data_sources/${dsId}`);
    // database 메타 + data_source properties 병합
    return { ...db, ...ds, database_id: dbId, data_source_id: dsId };
  }
  // DB ID가 아니라 DS ID가 직접 들어온 경우
  return call('GET', `/data_sources/${dbId}`);
}

async function updateDatabase(dbId, patch) {
  // patch = { properties: {...}, title: [...], icon: {...} }
  return call('PATCH', `/databases/${dbId}`, patch);
}

// DB ID → DS ID 캐시 (getDatabase로 자동 변환)
const _dsCache = new Map();

async function resolveDataSourceId(dbId) {
  if (_dsCache.has(dbId)) return _dsCache.get(dbId);
  const db = await getDatabase(dbId);
  const dsId = db.data_sources?.[0]?.id;
  if (!dsId) throw new Error(`data_source ID not found for database ${dbId}`);
  _dsCache.set(dbId, dsId);
  return dsId;
}

async function queryDatabase(dbId, { filter, sorts, pageSize = 100, startCursor } = {}) {
  const dsId = await resolveDataSourceId(dbId);
  const body = { page_size: pageSize };
  if (filter) body.filter = filter;
  if (sorts) body.sorts = sorts;
  if (startCursor) body.start_cursor = startCursor;
  return call('POST', `/data_sources/${dsId}/query`, body);
}

/** 모든 페이지를 자동 페이지네이션으로 가져오기 */
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

// ── 페이지 ───────────────────────────────────────────────
async function createPage(parentDbOrPageId, properties, { children, icon, cover, isDb = true } = {}) {
  if (!isDb) {
    const body = { parent: { type: 'page_id', page_id: parentDbOrPageId }, properties };
    if (children) body.children = children;
    if (icon) body.icon = icon;
    if (cover) body.cover = cover;
    return call('POST', '/pages', body);
  }
  // DB ID 또는 DS ID 모두 허용: database_id로 시도 → 실패 시 data_source_id로 재시도
  const body = { parent: { database_id: parentDbOrPageId }, properties };
  if (children) body.children = children;
  if (icon) body.icon = icon;
  if (cover) body.cover = cover;
  try {
    return await call('POST', '/pages', body);
  } catch (err) {
    if (err.status === 404) {
      body.parent = { data_source_id: parentDbOrPageId };
      return call('POST', '/pages', body);
    }
    throw err;
  }
}

async function getPage(pageId) {
  return call('GET', `/pages/${pageId}`);
}

async function updatePage(pageId, patch) {
  // 2026-03-11: archived → in_trash 자동 변환
  if ('archived' in patch) {
    patch.in_trash = patch.archived;
    delete patch.archived;
  }
  return call('PATCH', `/pages/${pageId}`, patch);
}

/** 페이지 본문을 마크다운 문자열로 조회 */
async function getPageMarkdown(pageId) {
  const res = await call('GET', `/pages/${pageId}/markdown`);
  return res.markdown ?? res;
}

/** 페이지 본문을 마크다운으로 전체 교체 */
async function updatePageMarkdown(pageId, markdown) {
  return call('PATCH', `/pages/${pageId}/markdown`, {
    type: 'replace_content',
    replace_content: { new_str: markdown },
  });
}

/** 페이지를 다른 부모로 이동 */
async function movePage(pageId, newParent) {
  // newParent: { page_id: '...' } | { database_id: '...' } | { type: 'workspace' }
  return call('POST', `/pages/${pageId}/move`, { parent: newParent });
}

// ── 코멘트 ───────────────────────────────────────────────
/** 페이지 또는 블록에 코멘트 생성 */
async function createComment(pageId, text, { blockId } = {}) {
  const body = {
    parent: { page_id: pageId },
    rich_text: [{ type: 'text', text: { content: text } }],
  };
  if (blockId) body.discussion_id = blockId;
  return call('POST', '/comments', body);
}

/** 페이지의 코멘트 목록 조회 */
async function listComments(pageId, { pageSize = 100, startCursor } = {}) {
  let url = `/comments?block_id=${pageId}&page_size=${pageSize}`;
  if (startCursor) url += `&start_cursor=${startCursor}`;
  return call('GET', url);
}

/** 코멘트 단건 조회 */
async function getComment(commentId) {
  return call('GET', `/comments/${commentId}`);
}

// ── 블록 ─────────────────────────────────────────────────
async function getBlocks(blockId, { pageSize = 100 } = {}) {
  return call('GET', `/blocks/${blockId}/children?page_size=${pageSize}`);
}

async function appendBlocks(blockId, children) {
  return call('PATCH', `/blocks/${blockId}/children`, { children });
}

async function deleteBlock(blockId) {
  return call('DELETE', `/blocks/${blockId}`);
}

// ── 블록 빌더 (헬퍼) ────────────────────────────────────
const block = {
  paragraph(text, opts = {}) {
    return {
      object: 'block',
      type: 'paragraph',
      paragraph: {
        rich_text: [{ type: 'text', text: { content: text, ...(opts.link ? { link: { url: opts.link } } : {}) } }],
        ...(opts.color ? { color: opts.color } : {}),
      },
    };
  },
  heading1(text) {
    return { object: 'block', type: 'heading_1', heading_1: { rich_text: [{ type: 'text', text: { content: text } }] } };
  },
  heading2(text) {
    return { object: 'block', type: 'heading_2', heading_2: { rich_text: [{ type: 'text', text: { content: text } }] } };
  },
  heading3(text) {
    return { object: 'block', type: 'heading_3', heading_3: { rich_text: [{ type: 'text', text: { content: text } }] } };
  },
  bullet(text) {
    return { object: 'block', type: 'bulleted_list_item', bulleted_list_item: { rich_text: [{ type: 'text', text: { content: text } }] } };
  },
  callout(text, emoji = '💡', color = 'default') {
    return {
      object: 'block',
      type: 'callout',
      callout: {
        icon: { type: 'emoji', emoji },
        rich_text: [{ type: 'text', text: { content: text } }],
        color,
      },
    };
  },
  divider() {
    return { object: 'block', type: 'divider', divider: {} };
  },
  toDo(text, checked = false) {
    return { object: 'block', type: 'to_do', to_do: { rich_text: [{ type: 'text', text: { content: text } }], checked } };
  },
  numbered(text) {
    return { object: 'block', type: 'numbered_list_item', numbered_list_item: { rich_text: [{ type: 'text', text: { content: text } }] } };
  },
  quote(text, color = 'default') {
    return { object: 'block', type: 'quote', quote: { rich_text: [{ type: 'text', text: { content: text } }], color } };
  },
  toggle(text, children = []) {
    return { object: 'block', type: 'toggle', toggle: { rich_text: [{ type: 'text', text: { content: text } }], children } };
  },
  code(text, language = 'plain text') {
    return { object: 'block', type: 'code', code: { rich_text: [{ type: 'text', text: { content: text } }], language } };
  },
  bookmark(url, caption = '') {
    const b = { url };
    if (caption) b.caption = [{ type: 'text', text: { content: caption } }];
    return { object: 'block', type: 'bookmark', bookmark: b };
  },
  equation(expression) {
    return { object: 'block', type: 'equation', equation: { expression } };
  },
  tableOfContents(color = 'default') {
    return { object: 'block', type: 'table_of_contents', table_of_contents: { color } };
  },
};

// ── 속성 빌더 (헬퍼) ────────────────────────────────────
const prop = {
  title(text) {
    return { title: [{ text: { content: text } }] };
  },
  richText(text) {
    return { rich_text: [{ text: { content: text } }] };
  },
  number(n) {
    return { number: n };
  },
  select(name) {
    return { select: { name } };
  },
  multiSelect(names) {
    return { multi_select: names.map(name => ({ name })) };
  },
  checkbox(checked) {
    return { checkbox: checked };
  },
  date(start, end) {
    const d = { start };
    if (end) d.end = end;
    return { date: d };
  },
  url(url) {
    return { url };
  },
  relation(ids) {
    return { relation: (Array.isArray(ids) ? ids : [ids]).map(id => ({ id })) };
  },
  status(name) {
    return { status: { name } };
  },
  email(email) {
    return { email };
  },
  phone(phone) {
    return { phone_number: phone };
  },
  people(ids) {
    return { people: (Array.isArray(ids) ? ids : [ids]).map(id => ({ object: 'user', id })) };
  },
};

// ── 파일 업로드 ──────────────────────────────────────────
// ref: padlet-to-notion-ext/popup/popup.js

const MIME_MAP = {
  '.webp': 'image/webp', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.svg': 'image/svg+xml',
  '.pdf': 'application/pdf', '.mp4': 'video/mp4', '.mp3': 'audio/mpeg',
};

/** File Upload API 전용 fetch (rate limit 재시도 포함) */
async function fileCall(method, path, body) {
  const isFormData = body instanceof FormData;
  for (let attempt = 0; attempt < 3; attempt++) {
    const headers = {
      'Authorization': `Bearer ${TOKEN}`,
      'Notion-Version': API_VERSION,
    };
    if (!isFormData) headers['Content-Type'] = 'application/json';
    const res = await fetch(`${BASE}${path}`, {
      method, headers,
      body: isFormData ? body : (body ? JSON.stringify(body) : undefined),
    });
    if (res.status === 429) {
      const wait = parseInt(res.headers.get('Retry-After') || '1', 10);
      await new Promise(r => setTimeout(r, wait * 1000));
      continue;
    }
    const data = await res.json();
    if (!res.ok) throw new Error(`Notion File API ${res.status}: ${data.message}`);
    return data;
  }
  throw new Error('Notion File API 요청 한도 초과 (3회 재시도 실패)');
}

/**
 * 로컬 파일을 Notion에 업로드
 * @param {string} filePath - 로컬 파일 경로
 * @returns {string} file_upload id (페이지 커버/블록에 사용)
 */
async function uploadFile(filePath) {
  const filename = basename(filePath);
  const ext = extname(filePath).toLowerCase();
  const contentType = MIME_MAP[ext] || 'application/octet-stream';
  const fileData = readFileSync(filePath);
  const size = statSync(filePath).size;
  if (size > 20 * 1024 * 1024) throw new Error(`파일 크기 초과 (20MB 제한): ${filename}`);

  // Step 1: 업로드 객체 생성
  const upload = await fileCall('POST', '/file_uploads', {
    filename, content_type: contentType,
  });

  // Step 2: 바이너리 전송 (FormData)
  const blob = new Blob([fileData], { type: contentType });
  const form = new FormData();
  form.append('file', blob, filename);
  await fileCall('POST', `/file_uploads/${upload.id}/send`, form);

  return upload.id;
}

/**
 * 파일을 업로드하고 페이지 커버로 설정
 * @param {string} pageId - 대상 페이지 ID
 * @param {string} filePath - 이미지 파일 경로
 */
async function setCover(pageId, filePath) {
  const uploadId = await uploadFile(filePath);
  return call('PATCH', `/pages/${pageId}`, {
    cover: { type: 'file_upload', file_upload: { id: uploadId } },
  });
}

/**
 * 파일을 업로드하고 이미지 블록으로 추가
 * @param {string} blockId - 부모 블록/페이지 ID
 * @param {string} filePath - 이미지 파일 경로
 */
async function addImageBlock(blockId, filePath) {
  const uploadId = await uploadFile(filePath);
  return call('PATCH', `/blocks/${blockId}/children`, {
    children: [{
      type: 'image',
      image: { type: 'file_upload', file_upload: { id: uploadId } },
    }],
  });
}

/**
 * URL에서 파일을 다운로드 후 Notion에 업로드
 * @param {string} url - 원본 파일 URL
 * @returns {string|null} file_upload id 또는 실패 시 null
 */
async function uploadFromUrl(url) {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const blob = await res.blob();
    if (blob.size > 20 * 1024 * 1024) return null;
    const contentType = blob.type || 'image/jpeg';
    const filename = new URL(url).pathname.split('/').pop()?.split('?')[0] || 'file';

    const upload = await fileCall('POST', '/file_uploads', {
      filename, content_type: contentType,
    });
    const form = new FormData();
    form.append('file', blob, filename);
    await fileCall('POST', `/file_uploads/${upload.id}/send`, form);
    return upload.id;
  } catch { return null; }
}

// ── 배치 유틸 ────────────────────────────────────────────
/**
 * 여러 작업을 동시성 제한으로 병렬 실행
 * Notion rate limit: 15분당 2,700콜 (평균 3/초), 버스트 허용
 * @param {Array} items - 처리할 항목 배열
 * @param {Function} fn - 각 항목에 적용할 async 함수
 * @param {number} concurrency - 동시 실행 수 (기본 15, 버스트 허용 범위)
 */
async function batch(items, fn, concurrency = 15) {
  const results = [];
  for (let i = 0; i < items.length; i += concurrency) {
    const chunk = items.slice(i, i + concurrency);
    const chunkResults = await Promise.allSettled(chunk.map(fn));
    results.push(...chunkResults);
  }
  return results;
}

// ── Upsert ───────────────────────────────────────────────

/** 속성값에서 비교용 plain text를 추출 */
function extractValue(page, propName) {
  const p = page.properties?.[propName];
  if (!p) return undefined;
  switch (p.type) {
    case 'title': return p.title?.[0]?.plain_text;
    case 'rich_text': return p.rich_text?.[0]?.plain_text;
    case 'number': return p.number;
    case 'select': return p.select?.name;
    case 'email': return p.email;
    case 'phone_number': return p.phone_number;
    case 'url': return p.url;
    default: return undefined;
  }
}

/** 속성 타입에 맞는 필터 객체 생성 */
function buildFilter(propName, propType, value) {
  const filterKey = propType === 'title' ? 'title'
    : propType === 'number' ? 'number'
    : propType === 'select' ? 'select'
    : 'rich_text';
  return { property: propName, [filterKey]: { equals: value } };
}

/** 429 재시도 래퍼 */
async function withRetry(fn, maxRetries = 2) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (err.status === 429 && attempt < maxRetries) {
        const wait = parseInt(err.response?.retry_after || '1', 10);
        await new Promise(r => setTimeout(r, wait * 1000));
        continue;
      }
      throw err;
    }
  }
}

/**
 * 단건 upsert: matchKey 속성값으로 기존 페이지를 찾아 업데이트하거나, 없으면 생성
 * 10건 미만일 때 사용 권장 (건당 API 2콜)
 * @param {string} dbId - 데이터베이스 ID
 * @param {string} matchKey - 매칭할 속성 이름
 * @param {string} matchType - 속성 타입: 'title' | 'rich_text' | 'number' | 'select'
 * @param {*} matchValue - 매칭할 값
 * @param {object} properties - 전체 속성 객체
 * @returns {{ action: 'created'|'updated', pageId: string }}
 */
async function upsertPage(dbId, matchKey, matchType, matchValue, properties) {
  return withRetry(async () => {
    const query = await queryDatabase(dbId, {
      filter: buildFilter(matchKey, matchType, matchValue),
      pageSize: 1,
    });
    if (query.results.length > 0) {
      const pageId = query.results[0].id;
      await updatePage(pageId, { properties });
      return { action: 'updated', pageId };
    } else {
      const page = await createPage(dbId, properties);
      return { action: 'created', pageId: page.id };
    }
  });
}

/**
 * 벌크 upsert: queryAll 캐시 + 높은 동시성으로 대량 처리
 * 10건 이상일 때 사용 권장 (건당 API 1콜 + queryAll 고정비용)
 *
 * 성능 참고 (테스트 2026-03-18):
 *   100건 upsert, 동시성 15 → 33.6초 (3.0건/초), 429 에러 0건
 *   vs 건바이건 쿼리 동시성 3 → 129.4초 (0.77건/초)
 *
 * @param {string} dbId - 데이터베이스 ID
 * @param {string} matchKey - 매칭할 속성 이름
 * @param {Array<{matchValue: *, properties: object}>} items - upsert 대상 배열
 * @param {object} [opts]
 * @param {number} [opts.concurrency=15] - 동시 실행 수
 * @param {Function} [opts.onProgress] - (done, total) => void
 * @returns {{ updated: number, created: number, failed: number, errors: string[] }}
 */
async function bulkUpsert(dbId, matchKey, items, { concurrency = 15, onProgress } = {}) {
  // 1. 전체 DB 캐시
  const allPages = await queryAll(dbId);
  const cache = new Map();
  for (const p of allPages) {
    const val = extractValue(p, matchKey);
    if (val != null) cache.set(String(val), p.id);
  }

  // 2. 캐시 기반 create/update
  const stats = { updated: 0, created: 0, failed: 0, errors: [] };
  for (let i = 0; i < items.length; i += concurrency) {
    const chunk = items.slice(i, i + concurrency);
    const settled = await Promise.allSettled(chunk.map(item =>
      withRetry(async () => {
        const existingId = cache.get(String(item.matchValue));
        if (existingId) {
          await updatePage(existingId, { properties: item.properties });
          return 'updated';
        } else {
          const page = await createPage(dbId, item.properties);
          // 새로 만든 페이지도 캐시에 추가 (같은 배치 내 중복 방지)
          cache.set(String(item.matchValue), page.id);
          return 'created';
        }
      })
    ));
    for (const s of settled) {
      if (s.status === 'fulfilled') stats[s.value]++;
      else { stats.failed++; stats.errors.push(s.reason?.message); }
    }
    if (onProgress) onProgress(Math.min(i + concurrency, items.length), items.length);
  }
  return stats;
}

// ── Export ────────────────────────────────────────────────
export const notion = {
  // raw
  call,
  API_VERSION,
  TOKEN,

  // search
  search,

  // database
  createDatabase,
  getDatabase,
  updateDatabase,
  queryDatabase,
  queryAll,

  // page
  createPage,
  getPage,
  updatePage,
  getPageMarkdown,
  updatePageMarkdown,
  movePage,

  // comment
  createComment,
  listComments,
  getComment,

  // block
  getBlocks,
  appendBlocks,
  deleteBlock,

  // file upload
  uploadFile,
  setCover,
  addImageBlock,
  uploadFromUrl,

  // upsert
  upsertPage,
  bulkUpsert,

  // helpers
  block,
  prop,
  batch,
  extractValue,
  withRetry,
};

export default notion;
