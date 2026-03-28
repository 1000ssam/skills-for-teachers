#!/usr/bin/env node
/**
 * Notion Page → Google Docs Converter
 *
 * Usage:
 *   node convert.js <notion-page-id> [google-doc-id] [--verbose]
 */

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

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('Usage: node convert.js <notion-page-id> [google-doc-id] [--verbose]');
    process.exit(0);
  }

  const positional = args.filter(a => !a.startsWith('--'));
  const verbose = args.includes('--verbose');
  const pageId = positional[0];
  const docId = positional[1] || null;

  console.log(`\n=== Notion → Google Docs 변환 시작 ===\n`);

  console.log('1. 노션 페이지 읽기...');
  const { markdown, title, supplementBlocks } = await readPage(pageId);

  console.log('2. 마크다운 파싱...');
  const blocks = parseNotionMarkdown(markdown, supplementBlocks);
  console.log(`   파싱 결과: ${blocks.length}개 블록`);
  if (verbose) {
    for (const b of blocks) {
      const preview = b.content?.slice(0, 50) || '(no content)';
      console.log(`   [${b.type}] depth=${b.depth} "${preview}..."`);
    }
  }

  let documentId = docId;
  if (!documentId) {
    console.log(`3. 새 Google Docs 생성: "${title}"...`);
    documentId = await createDocument(title);
  } else {
    console.log(`3. 기존 문서 사용: ${documentId}`);
  }

  console.log('4. batchUpdate 요청 생성...');
  const { requests, pendingTables } = buildRequests(blocks);
  console.log(`   요청 ${requests.length}개 생성 (테이블 ${pendingTables.length}개 대기)`);

  console.log('5. 메인 콘텐츠 삽입...');
  await executeRequests(documentId, requests);

  // 테이블 후처리
  if (pendingTables.length > 0) {
    console.log('6. 테이블 삽입...');
    // 6a) 플레이스홀더 → 네이티브 표로 교체
    const doc1 = await getDocument(documentId);
    const tableResult = buildTableRequests(doc1, pendingTables);
    if (tableResult.requests.length > 0) {
      await executeRequests(documentId, tableResult.requests);

      // 6b) 셀 내용 삽입
      console.log('   셀 내용 삽입...');
      const doc2 = await getDocument(documentId);
      const cellRequests = buildTableCellRequests(doc2, pendingTables);
      if (cellRequests.length > 0) {
        await executeRequests(documentId, cellRequests);
      }
    }
  }

  const docsUrl = `https://docs.google.com/document/d/${documentId}/edit`;
  console.log(`\n=== 변환 완료 ===`);
  console.log(`Google Docs: ${docsUrl}\n`);
}

main().catch(err => {
  console.error('변환 실패:', err.message);
  process.exit(1);
});
