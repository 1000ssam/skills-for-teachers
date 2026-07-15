#!/usr/bin/env python3
"""세특 초안 결정론 검증기 (Tier 1).

단건/폴더 초안을 받아 바이트·금지표현·점수패턴·명사형종결·특수문자·[판독불가]·영문과다를
전수 자동 점검하고, 폴더면 문장 유사도(개별성/템플릿화)까지 본다. 여기에 더해
**다신호 성취수준 추정기**(L1 천장 · L2 극성 · L4 자율성 · 하 보상 태도)로 상/중/하 힌트와
인플레/디플레·신호상충 플래그를 낸다. 전부 advisory(헌법4) — 자동 재작성 트리거 아님.
Tier 2(날조 가드·평가요소 정렬·근거 정박)는 LLM 심판 몫으로 SKILL.md Step6 참조.

사용:
  echo "본문" | python3 verify.py --max 650
  python3 verify.py drafts/ --max 650 --names names.txt --json
  python3 verify.py drafts/ --levels rubric.txt   # 파일별 루브릭등급(상/중/하) 주면 인플레/디플레 대조
"""
import argparse, json, os, re, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from neis_bytes import neis_bytes  # noqa: E402
import sentence_metrics  # noqa: E402  (문장 만연도 표면 신호 — advisory)

FORBIDDEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "forbidden-terms.txt")
RECOMMENDED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recommended-structure.txt")

SCORE_PATTERNS = [
    (r"\d+\s*점(?!검|화|검토|화\b)", "점수(X점)"),
    (r"\d+\s*등급", "등급"),
    (r"석차", "석차"),
    (r"백분위", "백분위"),
    (r"원점수", "원점수"),
    (r"\d+\s*%|\d+\s*퍼센트", "백분율"),
    (r"상위\s*\d+", "상위 %"),
    (r"만점", "만점"),
    (r"성취도\s*[A-E]\b|[A-E]\s*등급", "성취도 등급"),
]
# 특수문자·문단구분 기호(번호) — 물결(~)은 정상 한국어라 제외.
# 🚩 가운뎃점(·)은 아래 MIDDLE_DOT_PAT로 별도 하드플래그(세특 산문에서 나열 압축=AI slop).
SYMBOL_PAT = r"[①-⑳㉠-㉿▪•◦●○※★☆▶◆■□→⇒]"
NUMBERING_PAT = r"(?m)^\s*(?:\d+[.)]|[-*])\s+"
# 가운뎃점류(interpunct) — 세특은 산문이어야 하고 ·는 거의 항상 나열 구분자(AI slop)라
# 역할 모호성이 없어 하드플래그. 나열은 산문으로 풀어 쓴다(자동 치환 금지, 재작성은 LLM/사람).
# (• U+2022는 위 SYMBOL_PAT에 이미 포함되어 특수문자로 잡힘 → 여기서 중복 제외)
MIDDLE_DOT_PAT = r"[·‧・ㆍ∙･]"

# ── 성취수준 추정기 정규식 (어휘는 recommended-structure.txt, 패턴은 여기) ──
# (A) 능력 명사구 승화 패턴: 'X력/능력/역량 (을/이) … 갖춤/함양/보여줌/뛰어남/우수'
ABILITY_PAT = re.compile(
    r"(?:[가-힣]{1,4}력|능력|역량)\s*(?:을|이|은|는|의|에서|으로)?\s*"
    r"[가-힣\s,]{0,10}?(?:갖춤|기름|길러|함양|보여줌|보임|드러냄|발휘|뛰어남|뛰어난|우수|탁월|향상)")
# 완료·달성형 문말(상/중 정상): …함/임/봄/짐/움/냄 (ㅁ받침 종결)
COMPLETIVE_PAT = re.compile(r"(?:함|임|음|봄|짐|움|냄|킴)\.?\s*$")
# 잠재·조건·처방형 문말/구(하 신호)
PRESCRIPTIVE_PATS = [
    r"필요가\s*있", r"할\s*필요", r"필요해", r"필요하다", r"보완이\s*필요", r"길\s*필요",
    r"한다면", r"것으로\s*보(?:임|인다|여짐)", r"기회를\s*(?:가짐|제공|마련|가지)",
    r"기를\s*수\s*있", r"향상시킬\s*수\s*있", r"기대(?:됨|된다|해\s*봄)",
    r"노력이\s*(?:필요|요구)", r"았으면\s*(?:함|좋)", r"길러야",
]
PRESCRIPTIVE_RE = re.compile("|".join(PRESCRIPTIVE_PATS))

_LEVEL_ORD = {"상": 3, "중": 2, "하": 1}


def load_dict(path):
    """key|term1,term2,... → {key: [terms]} (주석·빈줄 무시)."""
    cats = {}
    if not os.path.exists(path):
        return cats
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        cat, terms = line.split("|", 1)
        cats[cat.strip()] = [t.strip() for t in terms.split(",") if t.strip()]
    return cats


load_forbidden = load_dict  # 하위호환 별칭


def _hits(text, terms):
    return [t for t in terms if t and t in text]


def last_hangul(s):
    for ch in reversed(s):
        if 0xAC00 <= ord(ch) <= 0xD7A3:
            return ch
    return None


def ends_in_mieum(syl):
    # ㅁ(16) 받침, 또는 ㄻ(10) 받침 — ㄹ어간 명사형(삶·앎·듦·만듦·베풂 등)도 정상 종결.
    return syl is not None and (ord(syl) - 0xAC00) % 28 in (16, 10)


def split_sents(text):
    return [s.strip() for s in re.split(r"\.", text) if len(s.strip()) >= 2]


def estimate_level(text, d):
    """다신호 성취수준 추정. d = recommended-structure.txt 사전. 결정론·advisory."""
    ability = _hits(text, d.get("ceiling.ability", []))
    adverb = _hits(text, d.get("ceiling.adverb", []))
    closer = _hits(text, d.get("ceiling.closer", []))
    ability_pat = len(ABILITY_PAT.findall(text))
    ceiling_total = len(ability) + len(adverb) + len(closer) + ability_pat

    auto_hi = _hits(text, d.get("autonomy.high", []))
    auto_lo = _hits(text, d.get("autonomy.low", []))

    sents = split_sents(text)
    completive = sum(1 for s in sents if COMPLETIVE_PAT.search(s))
    prescriptive = len(PRESCRIPTIVE_RE.findall(text))
    hedge = _hits(text, d.get("polarity.low", []))

    comp_all = d.get("compensation.attitude", [])
    comp_diag = [t for t in ("성실", "극복", "최선", "고군분투", "활력소", "꾸준", "책임감") if t in text]
    comp_hits = _hits(text, comp_all)

    floor = _hits(text, d.get("floor.core", []))
    growth = _hits(text, d.get("growth", []))

    # 근거 정박 프록시(L3, 부분 결정론): 수치·인용부호 밀도
    num = len(re.findall(r"\d", text))
    quote = len(re.findall(r"[「」『』‘’“”\"']", text))

    # ── 점수화(가중치는 KICE 등급쏠림 관찰 기반, 경험적) ──
    hi_score = ceiling_total * 1.0 + len(auto_hi) * 0.8 + min(completive, 4) * 0.2
    lo_score = len(auto_lo) * 1.2 + prescriptive * 1.0 + len(hedge) * 0.5 + len(comp_diag) * 0.5

    notes = []
    if not floor and not ceiling_total and not comp_hits and not growth:
        hint = "부실/불명 — 입력·보정 확인"
    elif ceiling_total == 0 and not auto_lo and prescriptive == 0 and len(hedge) <= 1:
        # 하의 정당한 서술 신호 = '진단' 태도어(성실·극복·최선…) 또는 성장 서사.
        # 중립 태도어(참여·관심·흥미)만으로는 '태도 서사 중심'으로 보지 않는다(상에도 흔함).
        if comp_diag or growth:
            # 능력승화 부재를 '단순나열'로 오탐하지 않는다(SYN 보상천장)
            hint = "하~중 — 태도·성장 서사 중심(능력승화 부재는 정상일 수 있음)"
        else:
            hint = "단순 나열/서술 의심 — 바닥만, 천장·근거 부재(p.101 지양)"
    else:
        if hi_score - lo_score >= 2.0:
            hint = "상 추정"
        elif lo_score - hi_score >= 1.5:
            hint = "하 추정"
        else:
            hint = "중 추정"

    # 신호 상충(인플레/디플레의 내부 프록시): 능력승화(상)와 지원발판/처방형(하) 혼재
    if ceiling_total >= 2 and (auto_lo or prescriptive):
        notes.append("신호상충: 능력승화(상)↔지원발판/처방형(하) 혼재 — 톤 일관성 점검")
    # 능력승화 없이 태도어만으로 상 톤을 흉내내는지(하 부풀림 주의)
    if ceiling_total == 0 and comp_diag and (adverb or closer):
        notes.append("태도어+칭찬 클로저이나 능력승화 부재 — 승화 대상 확인(능력 vs 태도)")

    hint_ord = 3 if hint.startswith("상") else (1 if hint.startswith("하") or "단순" in hint or "부실" in hint else (2 if hint.startswith("중") else None))
    return {
        "hint": hint, "hint_ord": hint_ord,
        "ceiling": {"ability": ability, "adverb": adverb, "closer": closer,
                    "pattern": ability_pat, "total": ceiling_total},
        "autonomy_high": auto_hi, "autonomy_low": auto_lo,
        "completive": completive, "prescriptive": prescriptive,
        "hedge": hedge, "compensation": comp_hits, "comp_diagnostic": comp_diag,
        "floor": floor, "growth": growth,
        "evidence": {"num": num, "quote": quote},
        "scores": {"hi": round(hi_score, 1), "lo": round(lo_score, 1)},
        "notes": notes,
    }


def check_draft(text, max_bytes, forbidden, recommended=None, names=None, rubric_level=None):
    flags = []
    b = neis_bytes(text)
    if max_bytes and b > max_bytes:
        flags.append(f"바이트초과: {b} > {max_bytes} (+{b - max_bytes})")

    # 금지표현
    for cat, terms in forbidden.items():
        hit = [t for t in terms if t in text]
        if hit:
            flags.append(f"금지표현[{cat}]: {', '.join(hit)}")

    # 점수·등급·석차
    for pat, label in SCORE_PATTERNS:
        m = re.search(pat, text)
        if m:
            flags.append(f"성적표현[{label}]: '{m.group().strip()}'")

    # 문체: 명사형 종결
    bad = []
    for s in split_sents(text):
        if not ends_in_mieum(last_hangul(s)):
            bad.append(s[-12:])
    if bad:
        flags.append(f"명사형종결위반({len(bad)}): …{' / …'.join(bad[:3])}")

    # 특수문자·번호기호
    syms = set(re.findall(SYMBOL_PAT, text))
    if syms:
        flags.append(f"특수문자: {' '.join(sorted(syms))}")
    if re.search(NUMBERING_PAT, text):
        flags.append("문단번호기호 사용")

    # 가운뎃점(나열 압축·AI slop) — 하드플래그. 나열은 산문으로 풀어 씀(자동수정 금지).
    dots = sorted(set(re.findall(MIDDLE_DOT_PAT, text)))
    if dots:
        flags.append(f"가운뎃점 사용({sum(text.count(d) for d in dots)}): {' '.join(dots)} — 나열은 산문으로")

    # [판독불가] 잔존
    n_unread = text.count("[판독불가]")
    if n_unread:
        flags.append(f"[판독불가] 잔존 {n_unread}건")

    # 실명/타인명
    if names:
        nhit = [nm for nm in names if nm and nm in text]
        if nhit:
            flags.append(f"이름삽입 의심: {', '.join(nhit)}")

    # 영문 과다
    eng = len(re.findall(r"[A-Za-z]", text))
    if eng > 15:
        flags.append(f"영문 과다({eng}자) — 한글 원칙 확인")

    # ── 문장 만연도(가독성) 표면 신호 — advisory (sentence_metrics.py) ──
    # 후보만 지목. 실제 재구성(관절 분할+문두 접속 복원+명사형 다양화)은 재작성 LLM 몫(D3).
    est = None
    struct = list(sentence_metrics.advisory_lines(text))

    # ── 성취수준 다신호 추정(advisory. 하드 위반 아님, 헌법4/2) ──
    if recommended:
        est = estimate_level(text, recommended)
        struct.append(f"성취수준 힌트: {est['hint']}  (천장{est['ceiling']['total']}/자율상{len(est['autonomy_high'])}/처방{est['prescriptive']}/헤지{len(est['hedge'])})")
        for nt in est["notes"]:
            struct.append(f"⚠ {nt}")
        # 루브릭 등급이 주어지면 인플레/디플레 대조(성취수준 앵커, 헌법)
        if rubric_level in _LEVEL_ORD and est["hint_ord"]:
            gap = est["hint_ord"] - _LEVEL_ORD[rubric_level]
            if gap >= 1:
                struct.append(f"⚠ 인플레 의심: 초안 톤({est['hint']}) > 루브릭({rubric_level})")
            elif gap <= -1:
                struct.append(f"⚠ 디플레 의심: 초안 톤({est['hint']}) < 루브릭({rubric_level})")

    return {"bytes": b, "flags": flags, "struct": struct, "est": est, "ok": not flags}


def shingles(text, n=2):
    t = re.sub(r"\s+", "", text)
    return set(t[i:i + n] for i in range(max(0, len(t) - n + 1)))


def similarity_pairs(items, threshold=0.6):
    out = []
    sh = {k: shingles(v) for k, v in items.items()}
    keys = list(sh)
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = sh[keys[i]], sh[keys[j]]
            if not a or not b:
                continue
            jac = len(a & b) / len(a | b)
            if jac >= threshold:
                out.append((keys[i], keys[j], round(jac, 2)))
    return sorted(out, key=lambda x: -x[2])


def load_levels(path):
    """파일별 루브릭 등급 맵: 'basename,상' 또는 'basename=중' 줄들."""
    m = {}
    if not path or not os.path.exists(path):
        return m
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"[,=\t]", line, 1)
        if len(parts) == 2:
            m[parts[0].strip()] = parts[1].strip()
    return m


def level_for(path, levels):
    if not levels:
        return None
    base = Path(path).name
    stem = Path(path).stem
    for k, v in levels.items():
        if k == base or k == stem or k in path:
            return v
    return None


def main():
    ap = argparse.ArgumentParser(description="세특 초안 결정론 검증기 (Tier 1)")
    ap.add_argument("paths", nargs="*", help="초안 txt/폴더 (없으면 stdin)")
    ap.add_argument("--max", type=int, default=650, help="바이트 상한(기본 650)")
    ap.add_argument("--names", help="실명 목록 파일(줄바꿈/쉼표 구분)")
    ap.add_argument("--levels", help="파일별 루브릭 등급(상/중/하) 맵 — 인플레/디플레 대조용")
    ap.add_argument("--sim-threshold", type=float, default=0.6, help="유사도 플래그 임계(자카드)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    forbidden = load_dict(FORBIDDEN_FILE)
    recommended = load_dict(RECOMMENDED_FILE)
    levels = load_levels(args.levels)
    names = None
    if args.names and os.path.exists(args.names):
        raw = Path(args.names).read_text(encoding="utf-8")
        names = [x.strip() for x in re.split(r"[,\n]", raw) if x.strip()]

    # 입력 수집
    items = {}
    if not args.paths:
        items["<stdin>"] = sys.stdin.read()
    else:
        for p in args.paths:
            pp = Path(p)
            if pp.is_dir():
                for f in sorted(pp.rglob("*.txt")):
                    items[str(f)] = f.read_text(encoding="utf-8", errors="replace")
            else:
                items[str(pp)] = pp.read_text(encoding="utf-8", errors="replace")

    results = {k: check_draft(v, args.max, forbidden, recommended, names, level_for(k, levels))
               for k, v in items.items()}
    sim = similarity_pairs(items, args.sim_threshold) if len(items) > 1 else []

    if args.json:
        print(json.dumps({"drafts": results, "similar_pairs": sim}, ensure_ascii=False, indent=2))
        return

    nflag = sum(1 for r in results.values() if not r["ok"])
    for k, r in results.items():
        tag = "OK" if r["ok"] else f"⚠️{len(r['flags'])}"
        print(f"[{tag}] {k}  ({r['bytes']}B)")
        for fl in r["flags"]:
            print(f"     - {fl}")
        for st in r.get("struct", []):
            print(f"     ~ {st}")
    if sim:
        print(f"\n[개별성] 유사쌍(≥{args.sim_threshold}):")
        for a, b, j in sim:
            print(f"     {j}  {a}  ~  {b}")
    print(f"\n요약: {len(results)}건 중 {nflag}건 하드플래그, 유사쌍 {len(sim)}건 "
          f"(성취수준 힌트는 advisory — 헌법4)")


if __name__ == "__main__":
    main()
