/**
 * Notion Reader — 마크다운 우선 읽기 + 블록 API 보충
 */

import { notion } from './notion-client.js';

/**
 * 페이지를 읽어 마크다운 + 보충 블록 데이터 반환
 */
export async function readPage(pageId) {
  // 메타데이터와 마크다운을 병렬 호출
  const [pageMeta, markdown] = await Promise.all([
    notion.call('GET', `/pages/${pageId}`),
    notion.getPageMarkdown(pageId),
  ]);

  // title 타입 속성을 자동 탐색 (DB마다 속성명이 다를 수 있음)
  const props = pageMeta.properties || {};
  const titleProp = Object.values(props).find(p => p.type === 'title');
  const title = titleProp?.title?.[0]?.plain_text || 'Untitled';
  console.log(`마크다운 읽기 완료 (${markdown.length} chars)`);

  // <unknown> 태그 발견 시에만 블록 API 보충
  let supplementBlocks = [];
  const unknowns = [...markdown.matchAll(/<unknown\s+[^>]*alt="([^"]+)"[^>]*>/g)];
  if (unknowns.length > 0) {
    console.log(`<unknown> 블록 ${unknowns.length}개 발견, 블록 API 보충 중...`);
    supplementBlocks = await fetchAllChildren(pageId);
  }

  return { markdown, title, supplementBlocks };
}

async function fetchAllChildren(blockId) {
  const allResults = [];
  let cursor;
  do {
    const path = `/blocks/${blockId}/children?page_size=100${cursor ? `&start_cursor=${cursor}` : ''}`;
    const res = await notion.call('GET', path);
    allResults.push(...res.results);
    cursor = res.has_more ? res.next_cursor : null;
  } while (cursor);
  return allResults;
}
