# learn-claude-code

Claude Code를 처음 쓰는 분을 위한 **단계별 학습 튜터**입니다.

환경과 수준을 물어본 뒤, 맞춤 학습 경로와 실전 예제를 함께 제공합니다.

---

## 설치

### 방법 1. 명령어 한 줄 (추천)

PowerShell을 열고 아래 명령어를 붙여넣은 뒤 Enter를 누르세요.

```powershell
irm https://raw.githubusercontent.com/1000ssam/skiils-for-teachers/main/skills/learn-claude-code/install.ps1 | iex
```

> **PowerShell 여는 방법:** `Win + R` → `powershell` 입력 → Enter

설치 후 **Claude Code를 재시작**하면 됩니다.

---

### 방법 2. 파일 직접 다운로드

1. **[메인 리포](https://github.com/1000ssam/skiils-for-teachers)** 로 이동합니다.
   > ⚠️ 이 페이지(개별 스킬 폴더)가 아닌, **메인 리포 첫 화면**으로 가야 합니다.

2. 초록색 **`<> Code`** 버튼 → **`Download ZIP`** 클릭

3. 다운로드된 ZIP 파일 압축 해제

4. 압축 해제한 폴더 안의 `skills\learn-claude-code` 폴더를 아래 경로에 복사합니다:
   ```
   C:\Users\{내 사용자 이름}\.claude\skills\
   ```
   > `.claude` 폴더가 안 보이면: 파일 탐색기 → **보기** → **숨긴 항목** 체크

5. Claude Code 재시작

---

## 사용법

Claude Code에서 이렇게 말하면 됩니다:

| 입력 | 동작 |
|------|------|
| `"Claude Code 배우고 싶어"` | 환경·수준 인터뷰 후 맞춤 학습 시작 |
| `"/learn-claude-code"` | 동일 (슬래시 커맨드) |
| `"/learn-claude-code 입문"` | 입문 경로로 바로 시작 |
| `"/learn-claude-code hooks"` | 특정 주제 바로 학습 |

---

## 학습 경로

| 수준 | 학습 내용 |
|------|----------|
| **입문** | Claude Code란? → 설치 → 작동 원리 → 기본 워크플로우 → 효과적인 프롬프트 |
| **중급** | 권한 관리 → 세션 관리 → CLAUDE.md → MCP 서버 → 단축키 |
| **고급** | 커스텀 스킬 → 훅(Hooks) → 서브에이전트 → 플러그인 → 비용 관리 |
