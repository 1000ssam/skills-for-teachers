/**
 * Image Utils — 이미지 접근 체크, 비지원 포맷 변환, Google Drive 임시 업로드
 *
 * Google Docs API insertInlineImage는 공개 접근 가능한 URL만 지원하고,
 * webp 등 일부 포맷을 지원하지 않는다.
 *
 * 워크플로:
 * 1) GET+Range로 접근/포맷 체크 (S3 signed URL은 HEAD 차단)
 * 2) 비지원 포맷(webp 등) → sharp로 jpg 변환
 * 3) 변환된 이미지를 Google Drive에 업로드 → 공개 URL 생성
 * 4) block.meta.url을 Drive URL로 교체
 */

import sharp from 'sharp';
import { getAccessToken } from './google-auth.js';

const SUPPORTED_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/bmp', 'image/svg+xml'];
const CONVERTIBLE_TYPES = ['image/webp', 'image/tiff', 'image/avif', 'image/heic'];

/**
 * 이미지 블록 배열을 받아 접근 체크 + 비지원 포맷 변환 처리
 * @param {Array} imageBlocks - type === 'image' && meta.url 이 있는 블록 배열
 */
export async function preprocessImages(imageBlocks) {
  if (imageBlocks.length === 0) return;

  console.log(`   이미지 ${imageBlocks.length}개 접근 체크...`);

  await Promise.all(imageBlocks.map(async (b) => {
    try {
      const res = await fetch(b.meta.url, {
        method: 'GET',
        headers: { Range: 'bytes=0-0' },
        signal: AbortSignal.timeout(5000),
      });

      const ct = (res.headers.get('content-type') || '').split(';')[0].trim();
      const isAccessible = res.ok || res.status === 206;

      if (!isAccessible) {
        b.meta._accessible = false;
        console.warn(`   ⚠️ 이미지 접근 불가 (${res.status}): ${b.meta.url.slice(0, 80)}...`);
        return;
      }

      if (SUPPORTED_TYPES.includes(ct)) {
        b.meta._accessible = true;
        return;
      }

      if (CONVERTIBLE_TYPES.includes(ct)) {
        console.log(`   🔄 ${ct} → jpeg 변환 중...`);
        const convertedUrl = await convertAndUpload(b.meta.url, ct);
        if (convertedUrl) {
          b.meta._originalUrl = b.meta.url;
          b.meta.url = convertedUrl;
          b.meta._accessible = true;
          b.meta._converted = true;
          console.log(`   ✅ 변환 완료`);
        } else {
          b.meta._accessible = false;
          console.warn(`   ⚠️ 이미지 변환 실패`);
        }
        return;
      }

      b.meta._accessible = false;
      console.warn(`   ⚠️ 미지원 이미지 포맷 (${ct}): ${b.meta.url.slice(0, 80)}...`);
    } catch {
      b.meta._accessible = false;
      console.warn(`   ⚠️ 이미지 접근 불가 (timeout): ${b.meta.url.slice(0, 80)}...`);
    }
  }));

  const total = imageBlocks.length;
  const ok = imageBlocks.filter(b => b.meta._accessible !== false).length;
  const converted = imageBlocks.filter(b => b.meta._converted).length;
  console.log(`   이미지 체크 완료: ${ok}/${total}개 사용 가능` + (converted > 0 ? ` (${converted}개 변환)` : ''));
}

/**
 * 이미지 다운로드 → sharp로 jpg 변환 → Google Drive 업로드 → 공개 URL 반환
 */
async function convertAndUpload(imageUrl, contentType) {
  const res = await fetch(imageUrl, { signal: AbortSignal.timeout(30000) });
  if (!res.ok) return null;
  const buffer = Buffer.from(await res.arrayBuffer());

  const jpegBuffer = await sharp(buffer).jpeg({ quality: 85 }).toBuffer();

  const driveUrl = await uploadToDrive(jpegBuffer, 'converted-image.jpg', 'image/jpeg');
  return driveUrl;
}

/**
 * Google Drive에 파일 업로드 후 공개 URL 반환
 */
async function uploadToDrive(buffer, filename, mimeType) {
  const token = await getAccessToken();

  const boundary = 'notion_to_docs_boundary';
  const metadata = JSON.stringify({ name: filename, mimeType });

  const body = Buffer.concat([
    Buffer.from(`--${boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n${metadata}\r\n--${boundary}\r\nContent-Type: ${mimeType}\r\n\r\n`),
    buffer,
    Buffer.from(`\r\n--${boundary}--`),
  ]);

  const uploadRes = await fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': `multipart/related; boundary=${boundary}`,
    },
    body,
  });

  if (!uploadRes.ok) {
    console.error('Drive 업로드 실패:', await uploadRes.text());
    return null;
  }

  const { id: fileId } = await uploadRes.json();

  const permRes = await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}/permissions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ role: 'reader', type: 'anyone' }),
  });

  if (!permRes.ok) {
    console.error('권한 설정 실패:', await permRes.text());
  }

  return `https://drive.google.com/uc?export=view&id=${fileId}`;
}

/**
 * 변환 중 생성된 임시 Drive 파일 정리
 */
export async function cleanupConvertedImages(imageBlocks) {
  const converted = imageBlocks.filter(b => b.meta._converted && b.meta.url);
  if (converted.length === 0) return;

  const token = await getAccessToken();
  for (const b of converted) {
    const match = b.meta.url.match(/id=([^&]+)/);
    if (!match) continue;
    try {
      await fetch(`https://www.googleapis.com/drive/v3/files/${match[1]}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` },
      });
    } catch { /* 정리 실패는 무시 */ }
  }
}
