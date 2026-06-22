# noninteractive-commands

Codex 작업 중 반복되는 **y/yes/enter 확인 프롬프트를 안전하게 줄이는 스킬**입니다.

명령어가 지원하는 `--yes`, `-y`, `--no-input`, `-Confirm:$false` 같은 비대화형 옵션을 우선 사용하고, 옵션이 없을 때만 제한된 횟수로 `y`를 입력합니다.

---

## 설치

### 방법 1. 명령어 한 줄 (추천)

PowerShell을 열고 아래 명령어를 붙여넣은 뒤 Enter를 누르세요.

```powershell
irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/noninteractive-commands/install.ps1 | iex
```

> **PowerShell 여는 방법:** `Win + R` → `powershell` 입력 → Enter

설치 후 **Codex를 재시작**하면 됩니다.

---

### 방법 2. 파일 직접 다운로드

1. **[메인 리포](https://github.com/1000ssam/skills-for-teachers)** 로 이동합니다.
   > 이 페이지(개별 스킬 폴더)가 아닌, **메인 리포 첫 화면**으로 가야 합니다.

2. 초록색 **`<> Code`** 버튼 → **`Download ZIP`** 클릭

3. 다운로드된 ZIP 파일 압축 해제

4. 압축 해제한 폴더 안의 `skills\noninteractive-commands` 폴더를 아래 경로에 복사합니다:
   ```text
   C:\Users\{내 사용자 이름}\.codex\skills\
   ```
   > `.codex` 폴더가 안 보이면: 파일 탐색기 → **보기** → **숨긴 항목** 체크

5. Codex 재시작

---

## 사전 준비

이 스킬은 **Codex**에서 사용합니다.

`auto_confirm.py` 보조 스크립트를 쓰려면 **Python 3**가 필요합니다. 대부분의 Codex 작업에서는 명령어 자체의 비대화형 옵션을 먼저 사용하므로 Python이 항상 필요한 것은 아닙니다.

---

## 사용법

Codex에서 이렇게 말하면 됩니다:

| 입력 | 동작 |
|------|------|
| `"작업 중 y를 계속 눌러야 하면 알아서 처리해줘"` | 명령별 비대화형 옵션 우선 적용 |
| `"yes 자동 입력으로 처리해줘"` | 안전한 경우 제한된 횟수만 stdin에 입력 |
| `"winget 약관 묻지 말고 진행해줘"` | `--accept-source-agreements`, `--accept-package-agreements` 사용 |
| `"npm create에서 y 안 묻게 해줘"` | `--yes` 또는 템플릿 옵션 사용 |
| `"삭제 확인도 전부 y 눌러줘"` | 파괴적 작업으로 보고 자동 승인하지 않음 |

---

## 처리 우선순위

| 순서 | 방식 | 예시 |
|------|------|------|
| 1 | 명령어가 제공하는 비대화형 옵션 사용 | `--yes`, `-y`, `--no-input`, `-Confirm:$false` |
| 2 | 선택값을 명령 인자로 명시 | `npm create vite@latest my-app -- --template react-ts` |
| 3 | 환경 변수를 좁은 범위에만 적용 | `CI=1`이 문서화된 도구 |
| 4 | 보조 스크립트로 제한된 입력만 전달 | `auto_confirm.py --answer y --repeat 1` |

---

## 직접 y를 넣어야 할 때

명령어에 `--yes` 같은 옵션이 없고, 프롬프트가 단순하며 안전한 경우에만 보조 스크립트를 사용합니다.

```powershell
python C:\Users\{내 사용자 이름}\.codex\skills\noninteractive-commands\scripts\auto_confirm.py --answer y --repeat 1 -- <명령어> <인자>
```

예시:

```powershell
python C:\Users\{내 사용자 이름}\.codex\skills\noninteractive-commands\scripts\auto_confirm.py --answer y --repeat 1 -- npm create vite@latest my-app
```

여러 번 입력해야 하는 프롬프트라면, 질문 개수를 확인한 뒤 `--repeat` 값을 지정합니다.

```powershell
python C:\Users\{내 사용자 이름}\.codex\skills\noninteractive-commands\scripts\auto_confirm.py --answer y --repeat 3 -- <명령어>
```

---

## 안전 규칙

이 스킬은 다음 작업을 일반적인 "y 대신 눌러줘" 요청으로 자동 승인하지 않습니다:

| 작업 | 처리 |
|------|------|
| 파일 삭제, 덮어쓰기 | 정확한 대상 확인 전 자동 승인 금지 |
| `git reset`, `git clean`, force push | 자동 승인 금지 |
| DB 삭제, 마이그레이션 | 자동 승인 금지 |
| 패키지 제거, 권한 변경 | 자동 승인 금지 |
| 결제, 배포, 운영 환경 변경 | 자동 승인 금지 |

`auto_confirm.py`는 `git reset`, `Remove-Item`, `kubectl delete`, `terraform destroy` 같은 위험 패턴을 기본적으로 차단합니다.

---

## 한계

- Codex 자체 승인 UI, 보안 프롬프트, trust 프롬프트를 우회하지 않습니다.
- 이미 다른 터미널에서 실행 중인 프로세스에 물리적으로 키보드 `y`를 누르지는 않습니다.
- 새로 실행하는 명령의 표준입력(stdin)에 제한된 답변을 넣는 방식입니다.
- 무제한 `yes | command` 방식은 기본으로 사용하지 않습니다.
