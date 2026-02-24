---
name: maily-subscribe
description: "Maily 뉴스레터 구독자를 등록하고 그룹을 관리합니다. 이메일 정보를 형태 불문하고 파싱하여 Maily API로 등록하며, 그룹 지정 시 신규/기존 구독자 모두 그룹에 추가합니다. writer_memo 슬러그 처리 및 중복 구독자 무시를 지원합니다. Use when: (1) 뉴스레터 구독자 등록, (2) Maily 구독자 추가, (3) 구독자 그룹 관리가 필요할 때."
allowed-tools: Bash(node *), Read, Write
---

# Maily Subscribe

## Overview

사용자가 던지는 이메일 정보를 파싱하여 Maily API로 구독자를 등록하고, 필요 시 그룹에 추가한다.

**런타임:** Node.js

## Config

**위치:** `~/.claude/skills/maily-subscribe/config.json`

```json
{
  "api_base": "https://api.maily.so",
  "newsletter_slug": "notiontalk",
  "api_token": "7oAs8pZznFcVgdHUwq4erSybS7vi7LC24nKt",
  "groups": {
    "그룹 한글명": "subscription_group_ext_id"
  }
}
```

`groups`는 그룹 이름(한글 가능) → Maily ext_id 매핑이다.
새 그룹이 생기면 Maily 대시보드 URL에서 ext_id를 확인하여 config.json에 추가한다.

## Workflow

Claude는 아래 순서를 **반드시** 따른다.

### Step 1. Config 읽기

`~/.claude/skills/maily-subscribe/config.json`을 읽어 `api_base`, `newsletter_slug`, `api_token`, `groups`를 로드한다.

### Step 2. 입력 파싱

사용자가 던진 텍스트에서 구독자 정보와 그룹 지정 여부를 추출한다. 형태는 자유롭다:
- 단순 이메일 목록
- "이름 / 이메일" 형태
- 표, JSON, 복붙한 스프레드시트 등 무엇이든

각 구독자에서 추출할 필드:
- `email` (필수)
- `name` (선택)
- `writer_memo` (선택) — 구독자의 특성/출처 메모

그룹 지정 파악:
- 사용자가 "XX 그룹에 추가", "XX 그룹으로" 등을 언급하면 그룹명 추출
- config의 `groups`에서 해당 이름으로 ext_id를 찾는다
- 그룹명이 config에 없으면 사용자에게 알리고 Maily 대시보드에서 ext_id 확인을 요청한다

### Step 3. writer_memo 처리

**`by-claude` 마킹 규칙 (필수):**
Claude가 등록하는 모든 구독자의 `writer_memo`에는 반드시 `_by-claude` 접미사를 붙인다.
- 메모가 없어서 기본값만 쓰는 경우: `"by-claude"`

**메모가 있는 경우:** 한국어/자연어 메모를 영문 슬러그로 변환한 뒤 `_by-claude`를 붙인다.
- 예: `"노션 강의 수강생"` → `"notion-class-student_by-claude"`
- 예: `"유튜브 댓글 이벤트 당첨자"` → `"youtube-comment-winner_by-claude"`
- 소문자, 하이픈 구분, 특수문자 제거

**메모가 없는 경우:** 사용자에게 질문한다:
```
이 구독자들의 writer_memo를 무엇으로 설정할까요?
(예: 출처, 경로, 특성 등. 슬러그로 변환 후 _by-claude가 자동으로 붙습니다)
```
답변을 받은 후 슬러그 변환 + `_by-claude` 접미사를 붙여 사용한다.

### Step 4. API 호출 (scripts/subscribe.mjs 실행)

```bash
node "C:/Users/user/.claude/skills/maily-subscribe/scripts/subscribe.mjs" \
  --config "C:/Users/user/.claude/skills/maily-subscribe/config.json" \
  --data "<JSON 문자열>" \
  [--group-id "<ext_id>"]
```

**스크립트 동작:**
1. 구독자를 순차적으로 POST 등록
   - 200 → 신규 등록 성공, 그룹 추가 대상
   - 422 → 기존 구독자, 그룹 추가 대상 (등록 스킵)
   - 429 → 1초 대기 후 최대 3회 재시도
   - 기타 → 실패 목록에 기록, 그룹 추가 건너뜀
2. `--group-id` 지정 시, 등록 성공 + 기존 구독자 **모두** 그룹에 추가
   - 신규/기존 구분 없이 전원 그룹 추가 시도
   - `marketing_agreement: true`, `marketing_agreed_at: 현재 시각` 항상 고정

### Step 5. 결과 보고

```
✅ 신규 등록:      N명
⏭️  기존 구독자:   N명
❌ 등록 실패:      N명
────────────────────────
📌 그룹 추가 성공: N명
📌 그룹 추가 실패: N명
```

## 그룹 ext_id 확인 방법

Maily 대시보드 → 구독자 → 그룹 선택 → URL에서 마지막 path segment가 ext_id
```
https://maily.so/notiontalk/o/m/subscription_groups/{ext_id}
```
확인한 ext_id를 config.json의 `groups`에 추가한다.

## Commands

| 사용자 입력 | 동작 |
|---|---|
| 이메일 목록 붙여넣기 | 파싱 후 등록만 |
| 이메일 목록 + "XX 그룹에 추가" | 등록 + 그룹 추가 |
| "XX 그룹 추가해줘" + 이메일 목록 | 등록 + 그룹 추가 |
| "새 그룹 등록해줘: 그룹명 / ext_id" | config.json groups에 추가 |

## Notes

- `marketing_agreement`는 항상 `true` 고정 (뉴스레터 등록 = 마케팅 동의)
- `welcome_letter`는 기본값(`true`) 사용 — 등록 즉시 웰컴 메일 발송됨
- 대량 등록 시 Rate Limit(초당 20회) 고려하여 스크립트가 자동 조절
- `writer_memo`에는 항상 `_by-claude` 접미사 필수 — Claude가 등록한 구독자 추적용
- 그룹 추가는 신규/기존 구독자 구분 없이 항상 시도 (기존 구독자도 그룹 추가 가능)
