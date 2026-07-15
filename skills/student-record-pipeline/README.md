# student-record-pipeline

학생 산출물(손글씨 활동지 스캔·사진·디지털 텍스트)을 받아 **교과세특(과목별 세부능력 및 특기사항) 초안 배치**를 만드는 엔드투엔드 파이프라인입니다.

단건 작성기 `student-record-writer`를 계승하되, 그 **앞에** 교사 인터뷰(인테이크 QA) → 입력 인제스천 → 명렬표 3중 대조 매핑 → 맥락 보정을, **뒤에** 바이트 예산 검증 → (NEIS 서식이 있으면) 결정론 이관을 붙였습니다. 반 전체를 한 번에 처리하지만 **최종본은 만들지 않습니다** — 언제나 '초안 + 상태'를 내고, 교사 눈검수를 NEIS 입력 전 필수 관문으로 둡니다.

> ⚠️ **기준 학년도 2026.** 학교생활기록부 기재요령은 매년 개정됩니다. 새 학년도에는 근거 파일(`references/giwan-*-grounding.md`)·바이트 규칙·금지어 목록을 갱신하세요.

---

## 왜 믿을 수 있나 (다른 세특 도구와 다른 점)

- **모든 규칙이 공식 문서에 정박** — 헌법·금지목록·글자수·문체·AI 조항은 **2026 기재요령**, 성취수준 어휘 사전은 **2022 개정 교육과정 별책 + KICE 세특 예시집**에서 결정론적으로 추출했습니다. 무출처 휴리스틱을 쓰지 않습니다. (근거 전체 지도: [`PROVENANCE.md`](PROVENANCE.md))
- **오매핑 0이 최우선** — 명렬표 정본 · 파일 순서 · OCR이 읽은 이름을 3중 대조해, 셋이 일치할 때만 자동 확정. 하나라도 어긋나면 교사에게 넘깁니다(엉뚱한 학생 세특 방지).
- **날조 금지** — 맥락 보정은 깨진 글자를 *올바로 읽는 사전* 역할일 뿐, 학생이 안 한 성취를 채워 넣지 않습니다. 못 읽는 곳은 `[판독불가]`.
- **결정론은 심판이 아니라 분류** — 바이트·금지어·점수표현·특수문자는 스크립트가 하드 판정하지만, 근거 정박·성취수준·날조 여부처럼 문맥이 필요한 것은 advisory 힌트로만 내고 최종 판단은 교사에게 둡니다.

---

## 설치 (이 스킬만)

아래 명령어는 **`student-record-pipeline` 하나만** `~/.claude/skills/`에 설치합니다. 다른 스킬은 건드리지 않습니다.

### 방법 1. 명령어 한 줄 (추천)

- **Windows** — PowerShell에 붙여넣고 Enter:
  ```powershell
  irm https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/student-record-pipeline/install.ps1 | iex
  ```
  > **PowerShell 여는 방법:** `Win + R` → `powershell` 입력 → Enter

- **macOS / Linux** — 터미널에 붙여넣고 Enter:
  ```bash
  curl -fsSL https://raw.githubusercontent.com/1000ssam/skills-for-teachers/main/skills/student-record-pipeline/install.sh | bash
  ```
  > **터미널 여는 방법 (Mac):** `Cmd + Space` → `터미널` 입력 → Enter

설치 후 **Claude Code를 재시작**하면 됩니다.

### 방법 2. 파일 직접 다운로드

1. [메인 리포](https://github.com/1000ssam/skills-for-teachers)에서 초록색 **`<> Code` → `Download ZIP`**.
   > ⚠️ 이 페이지(개별 스킬 폴더)가 아닌 **메인 리포 첫 화면**에서 받아야 합니다.
2. 압축을 풀고 `skills/student-record-pipeline` 폴더 **하나만** 아래 경로에 복사:
   - Windows: `C:\Users\{내 사용자 이름}\.claude\skills\`
   - macOS/Linux: `~/.claude/skills/`
   > `.claude` 폴더가 안 보이면: 파일 탐색기 → **보기** → **숨긴 항목** 체크
3. **Claude Code 재시작.**

### 방법 3. 리포를 이미 클론했다면 (로컬에서 복사)

```bash
# macOS / Linux
mkdir -p ~/.claude/skills
cp -rf skills/student-record-pipeline ~/.claude/skills/
```

```powershell
# Windows (PowerShell) — 클론한 리포 폴더에서 실행
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills" | Out-Null
Copy-Item -Recurse -Force .\skills\student-record-pipeline "$env:USERPROFILE\.claude\skills\"
```

> 다른 스킬까지 전부 설치하려면 [메인 리포 README](https://github.com/1000ssam/skills-for-teachers#전체-설치-모든-스킬-한-번에)의 전체 설치 명령어를 쓰세요.

---

## 쓰는 법

Claude Code에서 이렇게 말하면 됩니다:

| 입력 | 동작 |
|------|------|
| `"반 전체 세특 초안 만들어줘"` | **먼저 교사 인터뷰(인테이크 QA)**로 평가 맥락을 수집한 뒤 파이프라인 시작 |
| `"수행평가 산출물로 세특 써줘"` | 산출물 형태(스캔·사진·디지털)를 묻고 알맞은 입력 어댑터로 진행 |
| `"활동지 스캔해서 세특 만들어줘"` | 이미지 → 텍스트 전사 → 매핑 → 작성 → 검증 |

스킬이 **바로 작성으로 뛰지 않습니다.** 먼저 과제·루브릭·평가 렌즈·분량·명렬표 등을 1문1답으로 물어 '평가 맥락 스펙' 하나를 만들고, 그 스펙이 파이프라인 전체를 구동합니다. 과목이 바뀌면 이 스펙만 갈아끼웁니다.

---

## 6단계 (+ Step 7 NEIS 이관)

| 단계 | 하는 일 |
|---|---|
| **1. 인테이크 QA** | 교사 인터뷰로 평가 맥락 스펙 수집(과제·루브릭·평가 렌즈·분량·모델·문체) |
| **2. 인제스천** | 입력 어댑터로 학생 원문 텍스트 확보(아래 "입력은 무엇이든") |
| **3. 매핑** | 명렬표 3중 대조 → 확정/⚠️불일치/❌미제출 상태 부여(추측 확정 금지) |
| **4. 맥락 보정** | 스펙을 디코더로 써서 OCR 노이즈만 복원(보강·창작 금지) |
| **5. 세특 작성** | 4요소 구조(도달→과정·근거→역량→성장), 바이트 예산·명사형 종결·문체 프로파일 반영 |
| **6. 검증 & 출력** | Tier1 결정론 전수 + Tier2 LLM 적대적 심판 → **교사 검수 테이블** |
| **7. NEIS 이관** | (선택) NEIS 과목세특 내보내기 xlsx가 있으면 결정론 write-back(이중키·백업·라운드트립) |

각 단계의 규칙과 근거는 [`SKILL.md`](SKILL.md)에 있습니다.

### 입력은 무엇이든 (특정 OCR 벤더에 종속되지 않음)

- **① 디지털 텍스트**(구글폼·한글/워드·타이핑) → 그대로 직결.
- **② 스캔/사진 + 외부 OCR** → 임의 OCR로 추출(클로바·구글·네이버 등 무엇이든).
- **③ OCR이 없으면** → 담당 에이전트의 비전(멀티모달)으로 **축자 전사**(복사기 모드 — 오타 교정 금지, 못 읽으면 `[판독불가]`).

셋 다 동일한 하류 플로우로 합류합니다.

---

## 준비물

- **Python 3** (작성·검증·바이트 측정·문장 검출은 모두 표준 라이브러리만 사용).
- **Step 7(NEIS 이관)만** `openpyxl` 필요: `pip install openpyxl`. 이 단계를 안 쓰면 설치할 필요 없습니다.
- **명렬표 정본** — 가능하면 NEIS `과목별 세부능력 및 특기사항` 내보내기 xlsx를 주세요. 명렬표이자 최종 이관 타깃을 겸해, 완성본을 파일 하나로 되올릴 수 있습니다.

---

## 안전장치 — 헌법 6조 (절대 불변)

1. 매핑은 조용히 추측하지 않는다(3중 대조, 불일치 = 사람).
2. 보정은 복원까지만 — 보강·창작 금지(못 읽으면 `[판독불가]`).
3. 성취기준(침묵 근거)과 교사 평가 렌즈(표면)를 2층으로 쓴다.
4. 바이트 예산은 상한이지 하한이 아니다(분량 채우기 padding 금지).
5. 점수·등급·석차를 본문에 직접 쓰지 않는다.
6. 출력은 언제나 '초안 + 상태' — **교사 눈검수가 NEIS 입력 전 필수 관문.**

근거: 2026 기재요령은 "AI 생성물을 서술형 항목에 그대로 입력"하는 것을 금지하되, **윤문 등 보조 수단**으로 쓰고 최종 입력 전 허위·과장 여부를 확인하면 허용합니다. 이 스킬은 그 **검증을 강제하는 보조 수단**으로만 존재합니다.

---

## 폴더 구성

```
student-record-pipeline/
├── SKILL.md                          ← Claude Code가 따르는 파이프라인 정의(핵심)
├── README.md                         ← 이 문서
├── PROVENANCE.md                     ← 모든 규칙의 근거 지도(5원천 → 6단계 → 파일)
├── DESIGN-DECISIONS.md               ← 설계 원칙·한계·향후 과제
├── install.ps1 / install.sh          ← 이 스킬만 설치하는 스크립트(위 "설치")
└── references/
    ├── eval-context-spec.template.md ← 평가 맥락 스펙 빈 템플릿
    ├── giwan-2026-grounding.md       ← 2026 기재요령 발췌(페이지 인용)
    ├── neis-byte-rule.md             ← NEIS 바이트 규칙(공식)
    ├── forbidden-terms.txt           ← 금지표현 스캔 목록
    ├── recommended-structure.txt     ← 성취수준 다신호 어휘 사전(5층)
    ├── verify.py                     ← Tier1 결정론 검증 + 성취수준 추정
    ├── neis_bytes.py                 ← NEIS 바이트 결정론 계산
    ├── sentence_metrics.py           ← 만연·주술 관계 표면 신호(advisory)
    ├── test_sentence_metrics.py      ← 검출기 유닛테스트
    └── neis_writeback.py             ← Step 7 NEIS 결정론 이관(openpyxl)
```

`SKILL.md`만이 실제 동작을 정의합니다. 나머지는 근거·문서·보조 도구입니다.

---

## 라이선스

MIT License
