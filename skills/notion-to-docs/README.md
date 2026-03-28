# notion-to-docs

Notion 페이지를 Google Docs로 변환하는 Claude Code 스킬입니다.

## 설치

### macOS / Linux (WSL)

```bash
curl -fsSL https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/notion-to-docs/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/notion-to-docs/install.ps1 | iex
```

## 사전 준비

- **Node.js 18 이상** — https://nodejs.org
- **Notion Integration 토큰** — https://www.notion.so/profile/integrations
- **Google 계정** — 처음 실행 시 브라우저에서 로그인

## 사용법

Claude Code에서 이렇게 말하면 됩니다:

```
"이 노션 페이지 구글독스로 변환해줘 https://notion.so/..."
"노션 DB 일괄 변환해줘 https://notion.so/...?v=..."
```

### 첫 실행 시

1. Notion 토큰 입력 (1회)
2. Google 계정 연결 — 브라우저 팝업에서 "허용" 클릭 (1회)
3. 이후에는 URL만 주면 자동 변환

## 스타일

| Notion | Google Docs |
|--------|-------------|
| 제목 1 | Arimo 25pt 굵게 |
| 제목 2 | Arimo 16pt 굵게 |
| 제목 3 | Arimo 14pt 파란색 |
| 제목 4 | Arimo 12pt 파란색+밑줄 |
| 본문 | Arimo 10pt, 줄간격 150% |
| 콜아웃 | Notion 색상별 배경색 |
| 코드 | JetBrains Mono 9pt |
| 인용 | 이탤릭 + 왼쪽 테두리 |

스타일 변경: `scripts/style-map.js` 수정

## 문제 해결

### "config.json을 찾을 수 없습니다"
→ 첫 실행 시 자동 생성됩니다. Claude Code에서 "노션 문서 변환해줘"를 먼저 실행하세요.

### "Google 인증 필요" 팝업이 안 열림
→ 터미널에 출력된 URL을 직접 브라우저에 붙여넣으세요.

### Notion 페이지 접근 실패
→ Notion Integration이 해당 페이지에 연결되어 있는지 확인하세요.
  페이지 우측 상단 ··· → 연결 → 통합 이름 선택

### 이미지가 깨짐
→ Notion 이미지 URL은 1시간 후 만료됩니다. 변환 직후 확인하세요.
