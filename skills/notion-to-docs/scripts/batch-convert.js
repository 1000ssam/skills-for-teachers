#!/usr/bin/env node
/**
 * Notion DB → Google Docs 일괄 변환
 *
 * Usage: node batch-convert.js <db-id> [--verbose]
 * DB의 1레벨 하위 페이지를 모두 Google Docs로 변환한다.
 */

import { notion } from './notion-client.js';
import { readPage } from './notion-reader.js';
import { parseNotionMarkdown } from './markdown-parser.js';
import { buildRequests, buildTableRequests, buildTableCellRequests } from './request-builder.js';
import { createDocument, executeRequests } from './docs-executor.js';
import { getAccessToken } from './google-auth.js';

const DOCS_API = 'https://docs.googleapis.com/v1/documents';

async function getDocument(documentId) {
  const token = await getAccessToken();
  const res = await fetch(`${DOCS_API}/${documentId}?fields=body.content`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json();
}

async function convertPage(pageId) {
  const { markdown, title, supplementBlocks } = await readPage(pageId);
  const blocks = parseNotionMarkdown(markdown, supplementBlocks);

  const documentId = await createDocument(title);
  const { requests, pendingTables } = buildRequests(blocks);
  await executeRequests(documentId, requests);

  if (pendingTables.length > 0) {
    const doc1 = await getDocument(documentId);
    const tableResult = buildTableRequests(doc1, pendingTables);
    if (tableResult.requests.length > 0) {
      await executeRequests(documentId, tableResult.requests);
      const doc2 = await getDocument(documentId);
      const cellRequests = buildTableCellRequests(doc2, pendingTables);
      if (cellRequests.length > 0) {
        await executeRequests(documentId, cellRequests);
      }
    }
  }

  return { title, documentId, url: `https://docs.google.com/document/d/${documentId}/edit` };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.log('Usage: node batch-convert.js <db-id> [--verbose]');
    process.exit(0);
  }

  const dbId = args.filter(a => !a.startsWith('--'))[0];

  console.log(`\n=== DB 일괄 변환 시작 ===\n`);
  console.log(`DB 페이지 조회 중...`);

  const pages = await notion.queryAll(dbId);
  console.log(`${pages.length}개 페이지 발견\n`);

  const results = [];
  for (let i = 0; i < pages.length; i++) {
    const page = pages[i];
    const titleProp = Object.values(page.properties).find(p => p.type === 'title');
    const pageTitle = titleProp?.title?.[0]?.plain_text || 'Untitled';

    console.log(`[${i + 1}/${pages.length}] "${pageTitle}" 변환 중...`);
    try {
      const result = await convertPage(page.id);
      results.push(result);
      console.log(`   ✓ ${result.url}`);
    } catch (err) {
      console.error(`   ✗ 실패: ${err.message}`);
      results.push({ title: pageTitle, error: err.message });
    }
  }

  console.log(`\n=== 일괄 변환 완료 ===`);
  console.log(`성공: ${results.filter(r => r.url).length} / 실패: ${results.filter(r => r.error).length}\n`);
  for (const r of results) {
    if (r.url) console.log(`✓ ${r.title}: ${r.url}`);
    else console.log(`✗ ${r.title}: ${r.error}`);
  }
}

main().catch(err => {
  console.error('일괄 변환 실패:', err.message);
  process.exit(1);
});
