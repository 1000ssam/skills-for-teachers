# skills-for-teachers

한국 학교 교사를 위한 **Claude Code 스킬** 모음입니다.

공문서 정리, 수능 기출 분석, 인수인계서 작성, 교과세특 초안 작성 등 학교 행정·교육 업무를 자동화합니다.

---

## 스킬 목록

| 스킬 | 설명 | 자세히 |
|------|------|--------|
| **document-organizer** | 공문서 파일을 공문번호별로 자동 분류 | [README](skills/document-organizer/README.md) |
| **exam-analyzer** | 교과서 단원 × 수능 기출 매칭 → 분석표 + 문항 스크린샷 | [README](skills/exam-analyzer/README.md) |
| **handover-generator** | 공문 파일명 분석 → 업무 인수인계서 자동 생성 | [README](skills/handover-generator/README.md) |
| **student-record-writer** | 학생 산출물·관찰 메모 → 교과세특 초안 작성 | [README](skills/student-record-writer/README.md) |
| **learn-claude-code** | Claude Code 사용법 단계별 학습 튜터 | [README](skills/learn-claude-code/README.md) |
| **notion-pilot** | Notion API 통합 (DB/페이지/블록 CRUD, 파일 업로드, Upsert) | [README](skills/notion-pilot/README.md) |

---

## 전체 설치 (모든 스킬 한 번에)

> **PowerShell**을 열고 아래 명령어를 그대로 붙여넣은 뒤 Enter를 누르세요.

```powershell
irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/install.ps1 | iex
```

> **PowerShell 여는 방법:** `Win + R` → `powershell` 입력 → Enter

설치가 완료되면 **Claude Code를 재시작**하면 됩니다.

---

## 스킬 하나만 설치하고 싶다면

각 스킬의 README에서 개별 설치 명령어를 확인하세요.

---

## Claude Code가 없다면?

스킬을 사용하려면 **Claude Code**가 먼저 설치되어 있어야 합니다.
→ [Claude Code 설치 방법](https://docs.anthropic.com/ko/docs/claude-code)

---

## 라이선스

MIT License
