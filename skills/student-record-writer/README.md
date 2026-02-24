# student-record-writer

학생의 에세이, 탐구 보고서, 교사 관찰 메모를 바탕으로 **교과세특(과목별 세부능력 및 특기사항) 초안**을 작성합니다.

---

## 설치

### 방법 1. 명령어 한 줄 (추천)

PowerShell을 열고 아래 명령어를 붙여넣은 뒤 Enter를 누르세요.

```powershell
irm https://raw.githubusercontent.com/1000ssam/skiils-for-teachers/main/skills/student-record-writer/install.ps1 | iex
```

> **PowerShell 여는 방법:** `Win + R` → `powershell` 입력 → Enter

설치 후 **Claude Code를 재시작**하면 됩니다.

---

### 방법 2. 파일 직접 다운로드

1. **[메인 리포](https://github.com/1000ssam/skiils-for-teachers)** 로 이동합니다.
   > ⚠️ 이 페이지(개별 스킬 폴더)가 아닌, **메인 리포 첫 화면**으로 가야 합니다.

2. 초록색 **`<> Code`** 버튼 → **`Download ZIP`** 클릭

3. 다운로드된 ZIP 파일 압축 해제

4. 압축 해제한 폴더 안의 `skills\student-record-writer` 폴더를 아래 경로에 복사합니다:
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
| `"생기부 써줘"` / `"세특 작성해줘"` | 학생 텍스트를 요청한 후 세특 초안 작성 |
| `"이 보고서로 세특 써줘"` + 텍스트 붙여넣기 | 제공된 텍스트로 바로 세특 초안 작성 |
| `"이 파일로 생기부 써줘"` + 파일 경로 | 파일을 읽고 세특 초안 작성 |

---

## 출력 구조

**성취수준 → 수행 과정 → 역량 → 교사 총평** 4단계 구조로 교과세특 문구를 생성합니다.

기재요령 금지 사항(교외 수상, 공인어학성적, 학교명 등)을 자동 점검합니다.
