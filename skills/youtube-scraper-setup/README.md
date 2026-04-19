# youtube-scraper-setup

유튜브 채널의 신규 영상을 자동으로 수집하고, 자막(스크립트)을 추출하여 **Notion 데이터베이스**에 저장하는 프로젝트를 처음부터 세팅해주는 스킬입니다.

---

## 이런 분께 추천합니다

- 특정 유튜브 채널의 영상을 놓치지 않고 기록하고 싶은 분
- 영상 자막을 텍스트로 모아 검색·요약하고 싶은 분
- Notion AI와 연동하여 스크립트 보정·요약까지 자동화하고 싶은 분

---

## 주요 기능

### 대화형 세팅 — 말만 하면 완성

Claude Code에게 "유튜브 스크래퍼 만들어줘"라고 말하면, 환경 점검부터 코드 생성, Notion DB 구성, OS 스케줄러 등록까지 **8단계 워크플로**를 대화형으로 안내합니다.

### Notion DB 3가지 구성 옵션

| 옵션 | 설명 |
|------|------|
| **A) 자동 생성** | Notion API로 DB + 스킬 프롬프트 페이지를 원클릭 생성 |
| **B) 템플릿 복제** | 커스텀 뷰·필터가 포함된 완성형 템플릿을 복제 |
| **C) 기존 DB 사용** | 이미 사용 중인 DB에 연결 (스키마 자동 검증) |

### 자막 추출 + Notion 저장

- `yt-dlp`로 한국어 자막(자동 생성 포함)을 추출
- 영상 메타데이터(제목, 채널, 게시일, 썸네일) + 자막 전문을 Notion에 저장
- 로컬 마크다운 백업도 동시 생성

### Notion AI 스킬 연동

자동 생성(옵션 A) 또는 템플릿 복제(옵션 B) 선택 시, **오탈자 보정 + 요약 스킬 프롬프트**가 함께 생성됩니다. Notion AI 채팅에서 바로 사용할 수 있습니다.

### OS 스케줄러 자동 등록

- **Windows**: Task Scheduler (PowerShell 스크립트 제공)
- **macOS**: launchd (plist 파일 제공)
- **Linux**: crontab 안내

---

## 사전 요구사항

- **Node.js** v18 이상
- **yt-dlp** (`pip install yt-dlp`)
- **Notion Integration 토큰** ([발급 방법](https://www.notion.so/profile/integrations))

---

## 설치

### 방법 1. 명령어 한 줄 (추천)

#### macOS / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/youtube-scraper-setup/install.sh | bash
```

#### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/youtube-scraper-setup/install.ps1 | iex
```

### 방법 2. 수동 설치

1. 이 폴더의 `SKILL.md`를 다운로드합니다.
2. `~/.claude/skills/youtube-scraper-setup.md`로 저장합니다.

---

## 사용법

Claude Code를 열고 아래처럼 말하세요:

```
유튜브 스크래퍼 만들어줘
```

또는:

```
YouTube scraper 세팅해줘
```

Claude가 단계별로 안내합니다. 채널 URL, Notion 토큰, DB 설정 등을 대화로 진행하면 됩니다.

---

## 생성되는 파일 구조

```
your-project/
├── lib/
│   └── notion.mjs        # Notion API 헬퍼 (2026-03-11)
├── scrape.mjs             # 메인 스크래퍼
├── channels.json          # 구독 채널 목록
├── run.sh                 # 실행 래퍼 (로그 포함)
├── register-task.ps1      # Windows 스케줄러 (WSL)
├── .env                   # 토큰 (git 제외)
├── .env.example           # 토큰 템플릿
├── .gitignore
├── package.json
└── output/                # 로컬 마크다운 백업
    └── 2026-04-19/
        ├── index.md
        └── {videoId}.md
```

---

## Notion 워크스페이스 구조 (자동 생성 시)

```
[부모 페이지]
├── ### 영상과 스크립트를 수집한 후 아래 스킬을 발동시키면 더욱 좋습니다 :)
├── [SKILL]_유튜브_콘텐츠_요약    ← AI 스킬 프롬프트
├── ▶ 스킬 사용 방법              ← 토글 (사용법 안내)
├── ─────────────────
└── 🎬 YouTube 요약               ← 데이터베이스
```

---

## 라이선스

MIT
