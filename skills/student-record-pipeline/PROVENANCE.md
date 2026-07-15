# PROVENANCE — 원천·워크플로·참고자료 지도

이 스킬의 원칙은 **"휴리스틱 없이 전부 공식 문서에 정박"**이다. 이 문서는 그 근거가
어디서 왔고, 어느 단계에서 어느 파일로 쓰이는지의 단일 지도다.
(세션 인수인계는 `HANDOFF.md`, 파이프라인 규칙 본문은 `SKILL.md`.)

---

## 1. 근거 피라미드 (모든 것의 원천)

| # | 원천 (출처) | 무엇을 정박하나 | 산출 파일 |
|---|---|---|---|
| ① | **기재요령 2026** (경기 goe.go.kr + 고등판=경남 gne.go.kr, 223쪽) | 헌법 6조·금지목록·글자수·문체(명사형 종결)·AI조항·'평가요소' 공식개념 | `references/giwan-2026-grounding.md` (페이지 인용) |
| ② | **기재요령 고등판 p.214 각주 공식** | NEIS 바이트(한글3·영숫1·**엔터1**), 공통과목(예: 한국사)=1+2 **합산 500자**(1,500byte) | `references/neis-byte-rule.md` + `references/neis_bytes.py` |
| ③ | **2022 개정 교육과정 별책 37종** (보통교과 5~17=교육부 고시 2022-33호, 총론=국교위 2026-1호, 교양=2024-3호) | **바닥층** = 과정·기능 동사 72개 + 별책별 provenance·breadth | `harvest_report.json` → `references/recommended-structure.txt` |
| ④ | **KICE 「과정중심 평가와 연계한 교과 세부능력 및 특기사항」 고등 10과목** (국어·수학·영어·사회·역사·과학·도덕·음악·미술·체육; stas.moe.go.kr) | **천장·극성·자율성·보상층** = 약 570개 등급태그 예시(원천 코퍼스 286예시 결정론 스캔: 상104/중127/하55) | `analysis/*.md` + 코퍼스 json → `references/recommended-structure.txt` |
| ⑤ | **①~④ 종합** | **세특 품질 5층 모델** = 바닥·천장·극성·근거·자율성 + 🔑하의 '보상 천장'(태도·성장 서사) | `analysis/_SYNTHESIS.md` |

> ③④⑤의 **원천 데이터·분석물**(교육과정 별책·KICE 예시집·분석물)은 **스킬 밖 별도 작업폴더**에 둔다.
> 이 스킬 폴더는 버전관리·공유 대상 → 별책·KICE PDF·학생 실명 커밋 금지.

### 세특 품질 5층 (⑤ 요약 — 전문은 `_SYNTHESIS.md`)
- **L0 바닥**: 과정·기능 동사(분석·탐구·수행…). **등급 불변**, 존재=최소신호(부재=단순나열 의심). 과목별 꼬리 존재.
- **L1 천장**: 역량 승화 — **상 집중·하 소멸 = 진짜 품질**. 3형태 = (A)능력명사구 (B)질부사 (C)칭찬클로저.
- **L2 극성**: 완료형("~함") vs 잠재·처방형("~할 필요가 있음")+헤지 — **하 판별 최강, 결정론적**.
- **L3 근거**: 고유명·수치·인과 정박 밀도 상>중>하(역사 계량 상6.3>하2.8). 일부 결정론+Tier2.
- **L4 자율성**: 스스로(상) vs "도움을 받아·교사 지도·주어진 자료"(하) — 결정론적.
- **🔑 보상 천장**: 하는 능력천장 대신 **태도·성장 서사**로 대체(KICE 명문화). → **능력승화(상) vs 태도승화(하) 구별 필수.**

---

## 2. 6단계 워크플로 + 단계별 참고자료

```
[Step1 인테이크 QA]  교사 인터뷰로 '평가 맥락 스펙' 수집
      └ 참고: references/eval-context-spec.template.md · SKILL §2 질문세트 9개
[Step2 인제스천]     손글씨/사진 → OCR/비전 전사, 디지털 → 직결 (어댑터 교체 가능)
      └ 참고: Step2 3어댑터(디지털 직결 / 임의 OCR / 비전 축자전사)
[Step3 매핑]         명렬표 정본 ⟷ 파일순서 ⟷ OCR읽은값 3중대조
      └ 참고: 명렬표 정본(사용자 제공) · 헌법1(오매핑 0 최우선)
[Step4 맥락 보정]    스펙을 디코더로 OCR 노이즈만 복원(보강·창작 금지)
      └ 참고: §1 스펙 · 헌법2(복원까지만, 판독불가=플래그)
[Step5 세특 작성]    4요소 구조(도달→과정·근거→역량→종합·성장)
      └ 참고: references/recommended-structure.txt · student-record-writer 4단계 계승
[Step6 검증 2계층]   Tier1 결정론(전수) + Tier2 LLM 심판(적대적)
      └ 참고: references/verify.py · neis_bytes.py · forbidden-terms.txt · SKILL §6 프롬프트
```

**헌법 6조**(SKILL §0, 전부 ① 기재요령 근거): ①매핑 추측금지(3중대조) ②보정=복원만(날조금지)
③성취기준(침묵 근거)/평가요소(표면 렌즈) 2층 ④바이트=상한이지 하한아님 ⑤점수·등급 본문금지
⑥출력=초안+상태, 교사 눈검수가 NEIS 입력 전 필수 관문.

---

## 3. `references/` 파일별 원천 매핑

| 파일 | 역할 | 원천 |
|---|---|---|
| `giwan-2026-grounding.md` | 근거층 전체(8절, 페이지 인용) | ① 기재요령 2026 원문 |
| `neis-byte-rule.md` · `neis_bytes.py` | 바이트 결정론 계산 | ② 고등판 p.214 공식 |
| `forbidden-terms.txt` | Tier1 금지표현 스캔 | ① 기재요령 §5·§6 금지목록 |
| `eval-context-spec.template.md` | Step1 평가맥락 스펙 틀 | SKILL 설계(③ 평가요소 개념) |
| **`recommended-structure.txt`** | Tier1 성취수준 다신호 사전(17키) | **③ 별책 72동사 + ④ KICE 286예시 계량 + ⑤ SYN** — 항목마다 `[별책]/[KICE 상\|중\|하]/[SYN]` 주석 |
| **`verify.py`** | Tier1 검증기 + `estimate_level()` 다신호 추정기 | ①②③④⑤ 전부 로드 (금지=①, 바이트=②, 5층사전=③④⑤) |
| SKILL.md §6 Tier2 프롬프트 | LLM 심판(날조·근거정박·능력vs태도승화) | ⑤ SYN 보상천장 + 헌법2 |

### recommended-structure.txt 17키 구조
`floor.core` · `floor.process.high` · `floor.tail.{수학·과학·국어영어·예술·체육·도덕·사회역사}`
· `ceiling.ability` · `ceiling.adverb` · `ceiling.closer` · `polarity.low`
· `autonomy.low` · `autonomy.high` · `compensation.attitude` · `growth`

---

## 4. 외부 산출물 위치 (스킬 밖 별도 작업폴더)

- `harvest_all.py` · `harvest_report.json` — 별책 37종 하베스트(동사 72 + provenance).
- `analysis/_SYNTHESIS.md` — 10과목 종합 품질모델(반드시 읽을 것).
- `analysis/<과목>.md` × 10 — 과목별 정독 분석.
- `analysis/{exemplar,math,sci}_corpus.json` · `mi_blocks.json` · `moral_records.json` — 원천 태그 예시 코퍼스(286예시).
- 별책 37종 PDF · KICE 10과목 PDF — 최상위 원문.

---

## 5. 검증 커맨드

```bash
# Tier1 결정론 전수 검증 + 성취수준 다신호 추정
python3 references/verify.py <drafts_dir> --max 650 --names <명렬표.txt>
python3 references/verify.py <drafts_dir> --levels <루브릭등급.txt>   # 인플레/디플레 대조

# 바이트 결정론(공통과목=1·2 합산 500자 캡)
python3 references/neis_bytes.py <drafts_dir> --max 650 --min 500
```

---

## 부록 — 근거 정정 로그 (재발 방지)

- **HANDOFF v1 드롭리스트 오류(2026-07-12 정정)**: "고찰·규명·인과·구조화·개념화·입증·반박·자기주도·탐구심 드롭 확정"은 일부 오류.
  결정론 재스캔 결과 — **진짜 부재(드롭)**: 고찰·규명·개념화·입증·탐구심. **KICE 실재→드롭아님**: 반박(6회)→`floor.tail.사회역사`, 자기주도(4회 상)→`autonomy.high`.
  '인과'=코퍼스 7회 중 4회가 "원인과 결과" 부분문자열 오탐, 인과관계=0(용어로는 약함).
  → **교훈: 무출처 주장은 결정론 스캔으로 재검증 후 드롭한다(no-fabrication은 어휘 제거에도 적용).**
