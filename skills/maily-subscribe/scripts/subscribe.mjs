#!/usr/bin/env node
/**
 * Maily 구독자 등록 + 그룹 추가 스크립트
 * Usage: node subscribe.mjs --config <path> --data '<JSON>' [--group-id <ext_id>]
 */

import { readFileSync } from 'fs';
import { parseArgs } from 'util';

// ── CLI 인자 파싱 ──────────────────────────────────────────
const { values } = parseArgs({
  options: {
    config:   { type: 'string' },
    data:     { type: 'string' },
    'group-id': { type: 'string' },  // 선택: 그룹 ext_id
  }
});

if (!values.config || !values.data) {
  console.error("Usage: node subscribe.mjs --config <path> --data '<JSON>' [--group-id <ext_id>]");
  process.exit(1);
}

// ── Config 로드 ────────────────────────────────────────────
const config = JSON.parse(readFileSync(values.config, 'utf-8'));
const { api_base, newsletter_slug, api_token } = config;
const BASE_URL = `${api_base}/api/${newsletter_slug}`;
const groupId = values['group-id'] || null;

// ── 구독자 목록 파싱 ───────────────────────────────────────
const subscribers = JSON.parse(values.data);
// 기대 형식: [{ email, name?, writer_memo? }, ...]

// ── 유틸 ──────────────────────────────────────────────────
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

const authHeaders = {
  'Authorization': `Bearer ${api_token}`,
  'Content-Type': 'application/json',
};

// ── 구독자 등록 ────────────────────────────────────────────
async function registerSubscriber(subscriber) {
  const now = new Date().toISOString();
  const body = {
    email: subscriber.email,
    marketing_agreement: true,
    marketing_agreed_at: now,
  };
  if (subscriber.name) body.name = subscriber.name;

  // writer_memo: 항상 _by-claude 접미사 보장
  const memo = subscriber.writer_memo || '';
  body.writer_memo = memo
    ? (memo.endsWith('_by-claude') ? memo : `${memo}_by-claude`)
    : 'by-claude';

  const res = await fetch(`${BASE_URL}/subscriptions.json`, {
    method: 'POST',
    headers: authHeaders,
    body: JSON.stringify(body),
  });

  return { status: res.status, body: await res.json().catch(() => ({})) };
}

// ── 그룹에 구독자 추가 ─────────────────────────────────────
async function addToGroup(email, groupExtId) {
  const res = await fetch(
    `${BASE_URL}/subscription_groups/${groupExtId}/add_subscriber.json`,
    {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({ email }),
    }
  );
  return { status: res.status, body: await res.json().catch(() => ({})) };
}

// ── 메인 ──────────────────────────────────────────────────
const results = {
  registered:   [],  // 신규 등록 성공
  skipped:      [],  // 422: 이미 구독 중 (기존 구독자)
  failed:       [],  // 기타 에러
  groupAdded:   [],  // 그룹 추가 성공
  groupFailed:  [],  // 그룹 추가 실패
};

if (groupId) {
  console.log(`📋 그룹 추가 모드: ${groupId}\n`);
}

for (const subscriber of subscribers) {
  let isEligibleForGroup = false;
  let attempts = 0;

  // ── Step 1. 구독자 등록 ──
  while (true) {
    attempts++;
    const { status, body } = await registerSubscriber(subscriber);

    if (status === 200) {
      results.registered.push(subscriber.email);
      console.log(`✅ 등록: ${subscriber.email}`);
      isEligibleForGroup = true;
      break;

    } else if (status === 422) {
      // 이미 구독 중 → 그룹 추가는 여전히 진행
      results.skipped.push({ email: subscriber.email, reason: body.message || '422' });
      console.log(`⏭️  기존구독자: ${subscriber.email} (${body.message || '422'})`);
      isEligibleForGroup = true;
      break;

    } else if (status === 429) {
      if (attempts >= 3) {
        results.failed.push({ email: subscriber.email, reason: 'Rate limit 재시도 초과' });
        console.log(`❌ ${subscriber.email} (Rate limit 재시도 초과)`);
        break;
      }
      console.log(`⏳ ${subscriber.email} (Rate limit, 1초 대기...)`);
      await sleep(1000);

    } else {
      results.failed.push({ email: subscriber.email, reason: body.message || `HTTP ${status}` });
      console.log(`❌ ${subscriber.email} (${body.message || `HTTP ${status}`})`);
      break;
    }
  }

  // ── Step 2. 그룹 추가 (등록 성공 or 기존 구독자 모두 대상) ──
  if (groupId && isEligibleForGroup) {
    const { status, body } = await addToGroup(subscriber.email, groupId);
    if (status === 200) {
      results.groupAdded.push(subscriber.email);
      console.log(`   └─ 그룹 추가 ✅`);
    } else {
      results.groupFailed.push({ email: subscriber.email, reason: body.message || `HTTP ${status}` });
      console.log(`   └─ 그룹 추가 ❌ (${body.message || `HTTP ${status}`})`);
    }
    await sleep(50);
  }

  // 각 구독자 처리 사이 50ms 간격
  await sleep(50);
}

// ── 결과 요약 출력 ─────────────────────────────────────────
console.log('\n========== 결과 요약 ==========');
console.log(`✅ 신규 등록:         ${results.registered.length}명`);
console.log(`⏭️  기존 구독자:      ${results.skipped.length}명`);
console.log(`❌ 등록 실패:         ${results.failed.length}명`);

if (groupId) {
  console.log(`────────────────────────────────`);
  console.log(`📌 그룹 추가 성공:   ${results.groupAdded.length}명`);
  console.log(`📌 그룹 추가 실패:   ${results.groupFailed.length}명`);
}

if (results.failed.length > 0) {
  console.log('\n[등록 실패 목록]');
  results.failed.forEach(s => console.log(`  - ${s.email}: ${s.reason}`));
}

if (results.groupFailed.length > 0) {
  console.log('\n[그룹 추가 실패 목록]');
  results.groupFailed.forEach(s => console.log(`  - ${s.email}: ${s.reason}`));
}

if (results.failed.length > 0 || results.groupFailed.length > 0) process.exit(1);
