#!/usr/bin/env python3
"""문장 만연도(가독성) 표면 신호기 — verify.py(Tier-1)가 로드하는 advisory 모듈.

무엇을 하는가:
  세특 초안을 문장 단위로 갈라 **만연 의심 후보**를 지목한다. 신호는 전부 표면축
  (자수·연결신호 밀도·쉼표 밀도)이라 결정론이 참으로 셀 수 있다. 그러나 "어디서
  끊고 어떻게 이을지"는 의미축이므로 여기서 **판결하지 않는다** — 후보만 넘기고
  실제 재구성(관절 분할 + 문두 접속 복원 + 명사형 종결 다양화)은 재작성 LLM 몫이다.
  (SKILL.md §6 · DESIGN-DECISIONS.md D3: 결정론은 심판이 아니라 분류.)

왜 만연이 생기나(구조적 압박):
  ① 바이트 상한(예: 1,500B) 안에 근거를 다 담으려 문장을 쪼개지 않고 절로 압축.
  ② 명사형 종결('~함. ~함.') 단조를 피하려 한 문장에 다 몰아넣음(역효과=만연).
  → 처방은 "짧게 자르기"가 아니라 "복문을 읽기 좋은 리듬으로 재구성"이다.
     각 절의 논리 관계(근거→물음→결론)를 **문두 접속 표현**으로 살리고,
     의미로 묶인 절은 한 문장에 유지한다. 글자 수는 목표가 아니라 결과 지표.

쉼표 층위(중요):
  쉼표 밀도(쉼표 범벅)는 표면축이라 결정론이 '경고'할 수 있으나, **어느 쉼표를
  뺄지는 못 정한다**(리스트/병렬 경계 쉼표는 유지, 문두 접속어 뒤 쉼표는 생략 관행).
  후자만 `leading_comma`로 안전 후보 지목. 일반 쉼표 제거는 LLM 판단.

사용:
  echo "본문" | python3 sentence_metrics.py
  python3 sentence_metrics.py drafts/            # 폴더 전수
"""
import re
import sys
from pathlib import Path

# ── 임계값 (drafts/ 실측 분포로 캘리브레이션, advisory) ──
WARN_CHARS = 90      # 문장 자수(공백 제외) 경고 하한
TARGET_CHARS = 80    # 목표 상한 — 결과 지표이지 하드 컷 아님
WARN_CONN = 4        # 연결신호 밀도(며/면서/… + 쉼표) 경고 하한
WARN_COMMA = 4       # 쉼표 전용 밀도(쉼표 범벅) 경고 하한

# 문장 분할: 명사형 종결(한글)+마침표 경계. 세특은 명사형 종결이라 안전.
_SENT_SPLIT = re.compile(r"(?<=[가-힣])\.\s*")
# 연결신호(쉼표 제외 어절) — 쉼표는 별도 카운트해 합산
_CONN_RE = re.compile(r"며|면서|거쳐|들어|으로써|는데")
# 문두 접속 표현 — 관행상 뒤 쉼표 생략 가능(안전 제거 후보). 리스트/병렬 쉼표와 구분.
LEADING_CONNECTORS = [
    "나아가", "또한", "특히", "한편", "아울러", "그리고", "따라서", "그러므로",
    "이를 통해", "이를 바탕으로", "이를 실마리 삼아", "이를 계기로",
    "그 결과", "이처럼", "이렇게", "이와 함께", "이에", "그러나",
]
_LEADING_COMMA_RE = re.compile(
    r"^(?:" + "|".join(re.escape(c) for c in LEADING_CONNECTORS) + r")\s*,")

# 주술 관계: 세특의 (암묵) 주어는 항상 학생. 문장 최종 서술어가 학생의 인지·수행 동사
# (논술함·분석함·논증함·짚음·서술함…)여야 하고, 개념·사건 같은 무생물이 최종 서술어의
# 주어가 되면(예: "중화 개념이 …출발함") 학생이 사라진 문장이다. 분할(만연 교정) 과정에서
# "…출발하고 …정리함"을 끊으면 앞 조각이 "…출발함"이 되어 이 결함이 유입될 수 있다.
# 신호: 문장 최종 명사형이 '내용 전개' 자동사면 후보 지목. advisory(재서술은 LLM, D3).
#   · '-됨'류 피동/전성 종결(형성됨·강화됨·확립됨…): 학생은 '됨'의 주체가 아니므로 강신호.
#   · 능동 자동사 종결(출발함·성립함·굳어짐·이어짐…): 개념의 자체 전개를 서술 → 후보.
_PROCESS_ACTIVE_FINAL = {
    "출발함", "성립함", "굳어짐", "이어짐", "생겨남", "무너짐", "달라짐", "나타남",
    "변모함", "대두함", "번짐", "퍼짐", "뒤바뀜",
}


def final_predicate(s):
    """문장 최종 서술어(명사형) 어절. 예: '…출발함.' → '출발함'."""
    toks = s.split()
    return toks[-1].rstrip(".").strip() if toks else ""


def is_subject_predicate_risk(s):
    """개념·사건이 최종 서술어의 주어인지(주술 관계 미흡) 후보 판정. advisory."""
    fp = final_predicate(s)
    return fp.endswith("됨") or fp in _PROCESS_ACTIVE_FINAL


def visible_len(s):
    """공백 제외 자수(바이트 아님). NEIS 바이트는 neis_bytes.py 별도."""
    return len(re.sub(r"\s", "", s))


def split_sentences(text):
    return [s.strip() for s in _SENT_SPLIT.split(text.strip()) if len(s.strip()) >= 2]


def analyze_sentence(s):
    """한 문장의 표면 신호. 전부 advisory."""
    chars = visible_len(s)
    commas = s.count(",") + s.count("，")  # 반각·전각 쉼표
    conn = len(_CONN_RE.findall(s)) + commas  # 연결신호 밀도(쉼표 포함)
    reasons = []
    if chars >= WARN_CHARS:
        reasons.append(f"{chars}자")
    if conn >= WARN_CONN:
        reasons.append(f"연결{conn}")
    leading_comma = bool(_LEADING_COMMA_RE.search(s))
    return {
        "text": s,
        "chars": chars,
        "commas": commas,
        "connectors": conn,
        "verbose": bool(reasons),          # 자수 or 연결 밀도 초과
        "comma_flood": commas >= WARN_COMMA,
        "leading_comma": leading_comma,    # 문두 접속어+쉼표 = 안전 제거 후보
        "subject_pred": is_subject_predicate_risk(s),  # 개념·사건=주어(주술 미흡) 후보
        "final_pred": final_predicate(s),
        "reasons": reasons,
    }


def analyze_text(text):
    """문단 전체: 문장별 신호 + 요약. 결정론·advisory."""
    sents = [analyze_sentence(s) for s in split_sentences(text)]
    lens = [s["chars"] for s in sents]
    verbose = [s for s in sents if s["verbose"]]
    return {
        "sentences": sents,
        "verbose": verbose,
        "comma_flood": [s for s in sents if s["comma_flood"]],
        "leading_comma": [s for s in sents if s["leading_comma"]],
        "subject_pred": [s for s in sents if s["subject_pred"]],
        "summary": {
            "n_sent": len(sents),
            "avg": round(sum(lens) / len(lens), 1) if lens else 0,
            "max": max(lens) if lens else 0,
        },
    }


def advisory_lines(text):
    """verify.py 출력용 struct 문자열 목록(경고만). 하드플래그 아님."""
    a = analyze_text(text)
    out = []
    s = a["summary"]
    out.append(f"문장 {s['n_sent']} · 평균 {s['avg']}자 · 최장 {s['max']}자")
    if a["verbose"]:
        out.append(f"만연 의심 {len(a['verbose'])}문장 (목표 ≤{TARGET_CHARS}자, 재구성은 LLM 몫):")
        for v in a["verbose"]:
            head = v["text"][:30]
            tail = v["text"][-16:] if len(v["text"]) > 46 else ""
            sep = "…" if tail else ""
            out.append(f"  [{','.join(v['reasons'])}] {head}{sep}{tail}")
    if a["comma_flood"]:
        out.append(f"쉼표 범벅 {len(a['comma_flood'])}문장 (AI slop 신호 — 생략 가능한 쉼표 점검, 제거는 LLM)")
    if a["leading_comma"]:
        out.append(f"문두 접속어+쉼표 {len(a['leading_comma'])}건 (관행상 생략 가능 — 안전 제거 후보)")
    if a["subject_pred"]:
        out.append(f"주술 관계 점검 {len(a['subject_pred'])}문장 (개념·사건이 주어? 학생 행위로 재서술 권장, 재작성은 LLM):")
        for sp in a["subject_pred"]:
            out.append(f"  [최종서술어 '{sp['final_pred']}'] …{sp['text'][-24:]}")
    return out


def main():
    if len(sys.argv) < 2:
        text = sys.stdin.read()
        for ln in advisory_lines(text):
            print(ln)
        return
    total = 0
    for p in sys.argv[1:]:
        pp = Path(p)
        files = sorted(pp.rglob("*.txt")) if pp.is_dir() else [pp]
        for f in files:
            a = analyze_text(f.read_text(encoding="utf-8", errors="replace"))
            vcount = len(a["verbose"])
            total += vcount
            tag = f"만연{vcount}" if vcount else "OK"
            s = a["summary"]
            print(f"[{tag}] {f.name}  문장{s['n_sent']} 평균{s['avg']} 최장{s['max']}")
            for v in a["verbose"]:
                print(f"     ⚠ [{','.join(v['reasons'])}] {v['text'][:38]}…{v['text'][-18:]}")
            for c in a["comma_flood"]:
                if not c["verbose"]:
                    print(f"     ~ 쉼표{c['commas']} {c['text'][:38]}…")
    print(f"\n총 만연 후보: {total}문장")


if __name__ == "__main__":
    main()
