/**
 * Notion API 클라이언트 — notion-to-docs 스킬 전용
 *
 * notion-api.mjs에서 변환에 필요한 함수만 추출.
 * 토큰은 ../config.json에서 읽음.
 */

import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CONFIG_PATH = join(__dirname, '..', 'config.json');

const API_VERSION = '2026-03-11';
const BASE = 'https://api.notion.com/v1';

function loadToken() {
  let config;
  try {
    config = JSON.parse(readFileSync(CONFIG_PATH, 'utf-8'));
  } catch {
    throw new Error(
      'config.json을 찾을 수 없습니다. 먼저 Notion 토큰을 설정해 주세요.'
    );
  }
  if (!config.notion_token) {
    throw new Error(
      'config.json에 notion_token이 비어 있습니다. Notion 토큰을 설정해 주세요.'
    );
  }
  return config.notion_token;
}

// ── Base fetch ───────────────────────────────────────────

async function call(method, path, body) {
  const token = loadToken();
  const url = path.startsWith('http') ? path : `${BASE}${path}`;
  const res = await fetch(url, {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
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
    throw err;
  }
  return data;
}

// ── 페이지 마크다운 조회 ─────────────────────────────────

async function getPageMarkdown(pageId) {
  const res = await call('GET', `/pages/${pageId}/markdown`);
  return res.markdown ?? res;
}

// ── DB 조회 (queryAll) ──────────────────────────────────

const _dsCache = new Map();

async function resolveDataSourceId(dbId) {
  if (_dsCache.has(dbId)) return _dsCache.get(dbId);
  const db = await call('GET', `/databases/${dbId}`).catch(() => null);
  if (db?.data_sources?.[0]?.id) {
    const dsId = db.data_sources[0].id;
    _dsCache.set(dbId, dsId);
    return dsId;
  }
  // DB ID가 아니라 DS ID가 직접 들어온 경우
  return dbId;
}

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

// ── Export ───────────────────────────────────────────────

export const notion = {
  call,
  getPageMarkdown,
  queryAll,
};
