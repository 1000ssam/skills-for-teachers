# Configuration Structure

## config.json 위치

```
~/.claude/skills/document-organizer/config.json
```

## 구조

**최초 실행 시 자동 생성되는 구조:**

```json
{
  "version": "1.0",
  "default_profile": "work",
  "profiles": {
    "work": {
      "name": "기본 공문 폴더",
      "path": "(사용자가 지정한 경로)",
      "last_used": null
    }
  }
}
```

**프로필을 추가한 경우 예시:**

```json
{
  "version": "1.0",
  "default_profile": "work",
  "profiles": {
    "work": {
      "name": "기본 공문 폴더",
      "path": "(사용자가 지정한 경로 1)",
      "last_used": "2025-01-17T10:30:00Z"
    },
    "personal": {
      "name": "개인 공문 폴더",
      "path": "(사용자가 지정한 경로 2)",
      "last_used": null
    }
  }
}
```

## 필드 설명

| 필드 | 타입 | 설명 |
|---|---|---|
| `version` | string | 설정 파일 버전. 현재 `"1.0"` |
| `default_profile` | string | 기본 프로필 이름 |
| `profiles.<name>.name` | string | 프로필 표시명 (한글 가능) |
| `profiles.<name>.path` | string | 공문서 디렉토리 Windows 절대경로 |
| `profiles.<name>.last_used` | string\|null | 마지막 사용 시간 (ISO 8601) |

## 경로 규칙

- **Windows 절대경로만 허용:** 예: `C:\\Users\\username\\...`
- **JSON 내 역슬래시 이스케이프:** `\` → `\\`
- **금지:** `/c/Users/...` (Git Bash 스타일), 상대경로
- **기본값 없음:** 사용자가 최초 실행 시 지정한 경로가 곧 기본값

## 프로필 관리

프로필 추가/변경/삭제는 config.json을 직접 Edit 도구로 수정한다.

### 프로필 추가 예시
```json
"archive": {
  "name": "보관용 공문",
  "path": "(사용자가 지정한 보관 경로)",
  "last_used": null
}
```

### 기본 프로필 변경
`default_profile` 값을 원하는 프로필 이름으로 변경

### 설정 초기화
config.json 파일 삭제 → 다음 실행 시 재설정
