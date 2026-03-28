/**
 * Google Docs Executor — REST API 직접 호출
 *
 * gws CLI 의존성을 제거하고 Google Docs REST API를 직접 호출한다.
 * OAuth2 토큰은 google-auth.js에서 관리.
 */

import { getAccessToken } from './google-auth.js';

const DOCS_API = 'https://docs.googleapis.com/v1/documents';
const CHUNK_SIZE = 80;

async function docsRequest(method, path, body) {
  const token = await getAccessToken();
  const url = path.startsWith('http') ? path : `${DOCS_API}${path}`;
  const res = await fetch(url, {
    method,
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error(`Google Docs API ${res.status}: 응답 파싱 실패`);
  }
  if (!res.ok) {
    throw new Error(`Google Docs API ${res.status}: ${JSON.stringify(data.error || data)}`);
  }
  return data;
}

/**
 * 새 Google Docs 문서 생성
 */
export async function createDocument(title) {
  const data = await docsRequest('POST', '', { title });
  console.log(`문서 생성 완료: ${data.documentId}`);
  return data.documentId;
}

/**
 * batchUpdate 요청 실행 (자동 청크 분할)
 */
export async function executeRequests(documentId, requests) {
  if (requests.length === 0) return null;

  let lastResult = null;
  for (let i = 0; i < requests.length; i += CHUNK_SIZE) {
    const chunk = requests.slice(i, i + CHUNK_SIZE);
    const chunkNum = Math.floor(i / CHUNK_SIZE) + 1;
    const totalChunks = Math.ceil(requests.length / CHUNK_SIZE);
    if (totalChunks > 1) {
      console.log(`  청크 ${chunkNum}/${totalChunks} (${chunk.length}개 요청)...`);
    }
    lastResult = await docsRequest('POST', `/${documentId}:batchUpdate`, { requests: chunk });
  }
  return lastResult;
}
