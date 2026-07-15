#!/usr/bin/env python3
"""sentence_metrics.py + verify.py 가운뎃점/만연 신호 회귀 테스트.

의존성 없이 assert로 실행: python3 test_sentence_metrics.py
전부 표면축(결정론)이라 값이 고정. advisory 신호는 하드플래그가 아님을 함께 검증.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sentence_metrics as sm  # noqa: E402
import verify  # noqa: E402

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
    print(("  ok  " if cond else "FAIL  ") + msg)


# ── 1. 자수·분할 ──
check(sm.visible_len("가 나  다\n라") == 4, "visible_len 공백 제외")
check(len(sm.split_sentences("첫 문장을 정리함. 둘째 문장을 논증함.")) == 2, "명사형+마침표 2분할")

# ── 2. 만연 판정: 자수 임계 ──
long_s = "가" * 95
a = sm.analyze_sentence(long_s)
check(a["verbose"] and f"{95}자" in a["reasons"], "자수 ≥90 → verbose")
short_s = "가" * 70
check(not sm.analyze_sentence(short_s)["verbose"], "자수 70 → non-verbose")

# ── 3. 만연 판정: 연결신호 밀도(쉼표 포함) ──
conn_s = "가나, 다라, 마바, 사아를 정리하며 종합함"  # 쉼표3 + 며1 = 4
a = sm.analyze_sentence(conn_s)
check(a["verbose"] and a["connectors"] >= 4, "연결신호 ≥4 → verbose")

# ── 4. 쉼표 범벅 ──
flood = "가, 나, 다, 라, 마를 정리함"  # 쉼표4
check(sm.analyze_sentence(flood)["comma_flood"], "쉼표 ≥4 → comma_flood")
check(not sm.analyze_sentence("가와 나를 정리함")["comma_flood"], "쉼표 0 → non-flood")

# ── 5. 문두 접속어+쉼표 = 안전 제거 후보 ──
check(sm.analyze_sentence("나아가, 자신의 통념을 해체함")["leading_comma"], "문두 접속어+쉼표 탐지")
check(sm.analyze_sentence("이를 실마리 삼아, 되물음")["leading_comma"], "다어절 접속어+쉼표 탐지")
check(not sm.analyze_sentence("가나다, 라마바를 정리함")["leading_comma"], "일반 쉼표는 leading_comma 아님")

# ── 6. 문단 요약 ──
para = "짧은 문장임. " + "가" * 100 + ". 또 다른 문장을 정리함."
rep = sm.analyze_text(para)
check(rep["summary"]["n_sent"] == 3, "문단 문장 수")
check(rep["summary"]["max"] == 100, "문단 최장 자수")
check(len(rep["verbose"]) == 1, "문단 만연 후보 1")

# ── 7. advisory_lines: 문자열 목록·비예외 ──
lines = sm.advisory_lines(para)
check(isinstance(lines, list) and all(isinstance(x, str) for x in lines), "advisory_lines = str 목록")
check(any("만연 의심" in x for x in lines), "만연 라인 포함")

# ── 8. 가운뎃점 하드플래그(verify) — ·류 6종 ──
DOTS = ["·", "‧", "・", "ㆍ", "∙", "･"]  # U+00B7,2027,30FB,318D,2219,FF65
for d in DOTS:
    r = verify.check_draft(f"정치{d}경제를 분석함", 1500, {})
    check(any("가운뎃점" in f for f in r["flags"]) and not r["ok"],
          f"가운뎃점 하드플래그: U+{ord(d):04X}")

# ── 9. •(U+2022)는 가운뎃점 아닌 특수문자로 분리 ──
r = verify.check_draft("가• 나를 정리함", 1500, {})
check(any("특수문자" in f for f in r["flags"]) and not any("가운뎃점" in f for f in r["flags"]),
      "• 는 특수문자(가운뎃점 아님)")

# ── 8b. 주술 관계: 개념·사건이 최종 서술어 주어면 후보(주술 미흡) ──
check(sm.is_subject_predicate_risk("중화 개념이 주나라의 폄칭에서 출발함"), "개념+출발함 → 주술 후보")
check(sm.is_subject_predicate_risk("문화적 우월의식이 더해져 중화가 성립함"), "개념+성립함 → 주술 후보")
check(sm.is_subject_predicate_risk("한족 중심으로 폐쇄적 개념이 형성됨"), "'-됨' 종결 → 주술 후보")
check(not sm.is_subject_predicate_risk("중화 개념의 고착 과정을 재구성함"), "학생 동사(재구성함) → 정상")
check(not sm.is_subject_predicate_risk("사료를 꼼꼼히 정독하는 독해력을 보임"), "학생 동사(보임) → 정상")
check(sm.final_predicate("…과정을 서술함.") == "서술함", "최종 서술어 추출")
_sp = sm.analyze_text("중화 개념이 폄칭에서 출발함. 이를 학생이 논술함.")
check(len(_sp["subject_pred"]) == 1, "문단 주술 후보 카운트")

# ── 8c. 재서술 2형(실전 검증): 교정 전=후보, 교정 후=정상 ──
# 형A 목적어화(사례1) · 형B 내포절 '…했음을'(사례2·3). SKILL.md §주술 재서술 2형과 동기화.
_BEFORE = [
    "중화 개념이 주나라의 문명 자처와 융, 적, 만, 이의 폄칭에서 출발함",   # 사례1(개념 문두)
    "중국을 사방과 대비되는 중앙으로 보는 세계관에서 중화 개념이 출발함",   # 사례2(부사구+개념)
    "주변과 대비되는 중앙을 뜻하던 중국에 문화적 우월의식이 더해져 중화가 성립함",  # 사례3(부사구+개념)
]
_AFTER = [
    "중화 개념을 주나라의 문명 자처와 융, 적, 만, 이의 폄칭에서 출발한 것으로 서술함",   # 형A
    "중국을 사방과 대비되는 중앙으로 보는 세계관에서 중화 개념이 출발했음을 밝힘",       # 형B
    "주변과 대비되는 중앙을 뜻하던 중국에 문화적 우월의식이 더해져 중화가 성립했음을 파악함",  # 형B
]
for i, s in enumerate(_BEFORE):
    check(sm.is_subject_predicate_risk(s), f"실전 교정전{i+1} → 주술 후보(개념=주어)")
for i, s in enumerate(_AFTER):
    check(not sm.is_subject_predicate_risk(s), f"실전 교정후{i+1} → 정상(학생 동사 종결)")
# 형B는 자체전개 동사(출발/성립)를 비종결로 보존 — 절이 통째로 살아있는지 확인
check("출발했음" in _AFTER[1] and sm.final_predicate(_AFTER[1] + ".") == "밝힘",
      "형B: 자체전개 동사 보존 + 최종 서술어만 학생 동사")

# ── 9b. 명사형 종결: ㄹ어간 명사형(ㄻ받침 삶·앎·듦)도 정상 ──
for w in ["학습을 통해 앎", "역사를 삶", "깊게 파고듦", "직접 만듦"]:
    r = verify.check_draft(w + ".", 1500, {})
    check(not any("명사형" in f for f in r["flags"]), f"ㄻ 명사형 정상: …{w[-3:]}")
r = verify.check_draft("탐구를 진행했다.", 1500, {})  # 평서형 종결 = 위반
check(any("명사형" in f for f in r["flags"]), "평서형 종결은 명사형 위반")

# ── 10. 만연은 advisory — 하드플래그 아님(ok 유지) ──
clean_verbose = "중화 개념의 형성과 상대성을 " + "정밀하게 " * 30 + "정리함"  # 길지만 금지·기호 없음
r = verify.check_draft(clean_verbose, 999999, {})
check(r["ok"], "만연 문장이라도 하드플래그 없으면 ok=True(advisory)")
check(any("만연 의심" in s for s in r["struct"]), "만연은 struct(advisory)에만")

print()
if fails:
    print(f"❌ {len(fails)}개 실패:")
    for f in fails:
        print("   - " + f)
    sys.exit(1)
print("✅ 전체 통과")
