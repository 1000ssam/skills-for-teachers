#!/usr/bin/env python3
"""gate.py — 세특 자동 검사. 고쳐야 할 게 하나라도 있으면 실패로 끝난다.

여기에는 **답이 딱 떨어지는 검사만** 둔다. 글자 수가 넘었는지, 못 쓰는 말이
들어갔는지처럼 사람이 판단할 필요 없이 기계가 맞다/틀리다를 말할 수 있는 것들이다.

"이건 선생님이 한번 봐주셔야 합니다" 류는 검사가 아니라 숙제다. 그런 건 여기서
막지 않고 검수 엑셀의 '확인할 것' 칸으로 넘긴다.

  python3 tool/gate.py                      # 초안 전체 검사
  python3 tool/gate.py --source <확정.csv>  # 나이스에 넣기 직전 확정본 검사

다른 스크립트에서 가져다 쓸 때: check_text(글, 규칙) → (고쳐야 할 것[], 봐두실 것[])
"""
import argparse
import csv
import glob
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict

RED, YEL, GRN, CYN, DIM, RESET = (
    "\033[31m", "\033[33m", "\033[32m", "\033[36m", "\033[2m", "\033[0m")

CTRL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
NEWLINE = re.compile(r"[\r\n]")
# 가운뎃점류 6종 — 세특 산문에서 나열 압축은 AI slop
MIDDOT = re.compile(r"[·・･‧∙⋅]")
BULLET = re.compile(r"[①-⑳▶▷◆◇■□●○★☆※→←↔㉠-㉻]|^\s*[-*]\s", re.M)
# 점수·등급·석차 (헌법 5)
SCORE = re.compile(r"\d+\s*점|[A-E]\s*등급|성취수준\s*[A-E]\b|상위\s*\d+|\d+\s*등|\d+\s*/\s*\d+\s*등")
PERCENT = re.compile(r"\d+(\.\d+)?\s*%")
UNREADABLE = "[판독불가]"
# 문장 분리 — 소수점을 문장 끝으로 오인하지 않는다
SENT_SPLIT = re.compile(r"(?<!\d)\.(?!\d)")
# 명사형 종결 위반: 평서형 어미로 끝나는 문장
NON_NOMINAL = re.compile(r"(다|요|까|죠|네|군요|습니다|입니다)$")


def neis_bytes(s):
    """나이스가 세는 글자 크기: 한글·한자 3, 영문·숫자·공백 1 (기재요령 p.214 각주)."""
    return sum(3 if ord(ch) > 127 else 1 for ch in s)


def as_chars(nb):
    """바이트를 '한글 몇 자쯤'으로 바꿔 보여준다. 선생님은 자 수로 감을 잡으신다."""
    return nb // 3


def size_label(nb, byte_max):
    return f"{nb}바이트(한글 약 {as_chars(nb)}자) / 최대 {byte_max}바이트(약 {as_chars(byte_max)}자)"


# 동어반복 화이트리스트 — 어느 과목에서나 반복돼도 자연스러운 범용 구조어.
# 🚨 과목 주제어를 여기 박지 마라(과목마다 다르다). 주제어는 프로젝트의 repeat-whitelist.txt 가 준다.
WHITELIST_BASE = {"역량", "인식", "개인", "국가", "서사", "담론", "역사", "상상", "주류",
                  "자료", "서술", "문장", "학생", "활동", "내용", "생각", "부분", "사실"}
JOSA = (r"(으로써|으로|이라는|라는|에서|에게|께서|처럼|만큼|보다|부터|까지|마다|이나|하고"
        r"|와|과|을|를|이|가|은|는|의|에|로|도|만|께|나)$")


def repeat_stems(txt, rules):
    """같은 낱말이 조사만 바꿔 2회 이상 나오는지. ['위업×2', …] 을 돌려준다(경고용)."""
    from collections import Counter
    allow = WHITELIST_BASE | set(rules.get("repeat_whitelist") or [])
    stems = []
    for w in re.findall(r"[가-힣]{2,}", txt):
        t = re.sub(JOSA, "", w)
        t = re.sub(r"들$", "", t) or t          # 복수접미사 '들' 제거(백성들→백성)
        if len(t) >= 2 and t not in allow:
            stems.append(t)
    return [f"{w}×{c}" for w, c in sorted(Counter(stems).items(), key=lambda x: -x[1]) if c >= 2]


def check_text(txt, rules, name=""):
    """세특 한 편을 검사한다. (고쳐야 할 것[], 봐두실 것[]) 을 돌려준다.

    🔑 **규칙은 여기 한 곳에만 둔다.** 검사(이 파일)·검수 엑셀(make_review_xlsx.py)이 같은
    함수를 쓴다. 예전엔 마킹 화면도 자기 검사기(validate_draft.py)를 따로 갖고 있어서, 같은
    원고를 두고 화면은 '통과' 검사는 '하드 실패'라고 답했다. 그 화면 검수는 폐기했다
    (검수는 out/검수.xlsx 한 곳에서만 한다, 2026-08-06).
    """
    hard, soft = [], []
    byte_max = rules.get("byte_max", 1500)
    byte_short = rules.get("byte_short", 0)

    if not txt or not txt.strip():
        return [("빈칸", "세특이 비어 있습니다")], []

    nb = neis_bytes(txt)
    if nb > byte_max:
        hard.append(("길이", f"{size_label(nb, byte_max)} — "
                             f"한글 약 {as_chars(nb - byte_max)}자만큼 깁니다"))
    elif byte_short and nb < byte_short:
        soft.append(("짧음", f"{nb}바이트(한글 약 {as_chars(nb)}자) — "
                             f"학생이 쓴 내용이 적었다는 뜻일 수 있습니다. 고칠 일은 아닙니다"))

    # ① 기재요령 금지어 — 전 과목 공통·불변. **항상** 검사한다.
    #    예전에는 이 층이 아예 없어서, draft-rules.json 의 forbidden 을 안 채우면
    #    '교내대회 수상' 같은 문장이 그대로 통과했다(실측 2026-08-03).
    # giwan_ok = 이 과제에선 정상이라고 교사가 표시한 말. **경고만 끌 수 있고 하드 실패는 못 끈다.**
    # (예: 자료 비교 과제에서 '출판'은 출판사 이름으로 매번 나온다 — 매번 경고면 소음이다)
    ok = set(rules.get("giwan_ok", []))
    for cat, w, is_hard in rules.get("giwan", []):
        if w in txt:
            if is_hard:
                hard.append(("못 쓰는 말", f"'{w}'({cat}) — 기재요령상 어떤 항목에도 쓸 수 없습니다"))
            elif w not in ok:
                soft.append(("문맥 확인", f"'{w}'({cat}) — 학생이 **읽은** 자료를 가리키면 정상입니다. "
                                          f"학생 본인의 실적이면 빼야 합니다"))
    # ② 이 과제 전용 금지어 — 배치마다 다르다. 비어 있어도 정상이다.
    for w in rules.get("forbidden", []):
        if w in txt:
            hard.append(("못 쓰는 말", f"'{w}' — 이 과제에서 쓰지 않기로 하신 말입니다"))
    for w in rules.get("soft", []):
        if w in txt:
            soft.append(("조심할 말", f"'{w}' — 앞뒤 문맥을 한번 봐주세요"))

    if m := SCORE.search(txt):
        hard.append(("점수·등급", f"'{m.group()}' — 점수나 등수는 세특에 쓸 수 없습니다"))
    if m := PERCENT.search(txt):
        soft.append(("퍼센트", f"'{m.group()}' — 학생이 인용한 통계면 괜찮고, "
                               f"성적이면 빼야 합니다"))

    if m := MIDDOT.search(txt):
        hard.append(("가운뎃점(·)", f"'{m.group()}' — 나열을 점으로 묶지 말고 "
                                    f"문장으로 풀어 써야 합니다"))
    if m := BULLET.search(txt):
        hard.append(("특수기호", f"'{m.group().strip()}' — 번호나 불릿은 세특에 쓰지 않습니다"))
    if UNREADABLE in txt:
        hard.append(("안 읽힌 글자", f"'{UNREADABLE}' 가 그대로 남아 있습니다 — "
                                     f"학생 원본을 확인해 주세요"))

    if NEWLINE.search(txt):
        hard.append(("줄바꿈", "줄바꿈이 들어 있습니다 — 나이스에 붙여넣을 때 줄이 갈라집니다"))
    if "\t" in txt:
        hard.append(("탭 문자", "탭이 들어 있습니다"))
    if CTRL.search(txt):
        hard.append(("이상한 문자", "화면에 안 보이는 문자가 섞여 있습니다"))
    if txt != txt.strip():
        hard.append(("띄어쓰기", "맨 앞이나 맨 뒤에 공백이 있습니다"))
    if "  " in txt:
        hard.append(("띄어쓰기", "공백이 두 칸 이상 이어진 곳이 있습니다"))
    if emo := [c for c in txt if unicodedata.category(c) == "So"]:
        hard.append(("특수기호", f"그림문자 {len(emo)}개가 있습니다: {''.join(emo[:5])}"))

    for s in (x.strip() for x in SENT_SPLIT.split(txt)):
        if s and NON_NOMINAL.search(s):
            hard.append(("문장 끝맺음", f"'-함' '-임' 같은 형태로 끝나야 합니다: …{s[-18:]}"))
            break

    # 아래 셋은 예전에 화면 검사기에만 있던 것 — 규칙을 한 곳으로 모으며 옮겨 왔다.
    if re.search(r'[\u201c\u201d\u2018\u2019"\']{1}.{2,}[\u201c\u201d\u2018\u2019"\']{1}', txt):
        soft.append(("인용부호", "직접 인용부호 흔적이 있습니다 — 인용은 쓰지 않기로 했습니다"))
    if name and name in txt:
        soft.append(("본인 이름", f"'{name}' 이 문장에 들어 있습니다 — 세특에 학생 이름은 넣지 않습니다"))
    for r in repeat_stems(txt, rules):
        soft.append(("반복되는 말", f"{r} — 같은 말이 되풀이됩니다"))

    return hard, soft


def parse_key(hb):
    """5자리 학번 10401 → (반4, 번호1). 실패 시 None."""
    hb = str(hb).strip()
    return (int(hb[1:3]), int(hb[3:5])) if len(hb) == 5 and hb.isdigit() else None


GIWAN_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "forbidden-terms.txt"),
    os.path.join(os.path.expanduser("~/.claude/skills/student-record-pipeline"),
                 "references", "forbidden-terms.txt"),
]


def load_giwan():
    """기재요령 금지어 — (카테고리, 용어, 하드실패인가) 목록.

    배치 설정과 **별개 층**이다. draft-rules.json 의 forbidden 은 그 과제에서만 쓰는 것이라
    비어 있는 게 정상이지만, 이건 전 과목 공통이라 비면 안 된다. 한 칸에 합쳐 뒀더니
    뒤쪽을 지키려고 비운 기본값 때문에 앞쪽까지 같이 비었다(실측 2026-08-03).
    """
    for p in GIWAN_PATHS:
        if not os.path.exists(p):
            continue
        out = []
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "|" not in line:
                continue
            cat, terms = line.split("|", 1)
            is_hard = cat.startswith("*")
            cat = cat.lstrip("*")
            out += [(cat, t.strip(), is_hard) for t in terms.split(",") if t.strip()]
        return out
    print(f"{YEL}⚠️ 기재요령 금지어 목록(forbidden-terms.txt)을 못 찾았습니다 — "
          f"그 검사는 건너뜁니다{RESET}", file=sys.stderr)
    return []


def load_rules(path):
    if not os.path.exists(path):
        print(f"{YEL}⚠️ {path} 가 없습니다 — 최대 길이를 1500바이트(약 500자)로 잡고, "
              f"이 과제 전용 금지어 검사는 건너뜁니다{RESET}", file=sys.stderr)
        r = {"byte_max": 1500}
    else:
        r = {k: v for k, v in json.load(open(path, encoding="utf-8")).items()
             if not k.startswith("_")}
    r["giwan"] = load_giwan()          # 배치 설정과 무관하게 항상 붙는다
    # 동어반복 면제 주제어 — 과목마다 다르므로 프로젝트가 공급한다(없으면 빈 목록).
    wl = os.path.join(os.path.dirname(os.path.abspath(path)) or ".", "repeat-whitelist.txt")
    if os.path.exists(wl):
        with open(wl, encoding="utf-8") as f:
            r["repeat_whitelist"] = [ln.strip() for ln in f
                                     if ln.strip() and not ln.startswith("#")]
    return r


def load_records(args):
    """(학번, 이름, 세특) 목록. --source 있으면 CSV, 없으면 초안 폴더."""
    if args.source:
        with open(args.source, encoding="utf-8-sig", newline="") as f:
            return [(r["학번"].strip(), r.get("이름", "").strip(), r.get("세특") or "")
                    for r in csv.DictReader(f)]
    # 이름 출처는 여러 곳일 수 있다. 하나라도 있으면 쓰고, 다 없으면 학번만 찍히는데
    # 그러면 선생님이 누구 얘긴지 못 알아본다 — 그래서 마지막에 경고를 낸다.
    names = {}
    for path in (args.roster, os.path.join("out", "mapping_reconciled.csv")):
        if names or not os.path.exists(path):
            continue
        with open(path, encoding="utf-8-sig") as f:
            names = {r["학번"].strip(): (r.get("이름") or "").strip()
                     for r in csv.DictReader(f) if r.get("학번")}
    if not names:  # 표시 기록에도 이름이 들어 있다
        for fp in glob.glob(os.path.join("out", "marks", "*.json")):
            if os.path.basename(fp).startswith("_"):
                continue
            try:
                m = json.load(open(fp, encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if m.get("hakbun"):
                names[str(m["hakbun"]).strip()] = (m.get("name") or "").strip()
    if not names:
        print(f"{YEL}⚠️ 이름을 찾을 곳이 없어 학번만 표시합니다 "
              f"({args.roster} 도 out/mapping_reconciled.csv 도 없음){RESET}", file=sys.stderr)
    out = []
    for fp in sorted(glob.glob(os.path.join(args.drafts, "*.json"))):
        d = json.load(open(fp, encoding="utf-8"))
        hb = d.get("hakbun") or os.path.basename(fp)[:-5]
        out.append((hb, names.get(hb, ""), d.get("setuk") or ""))
    return out


def main():
    ap = argparse.ArgumentParser(description="세특 자동 검사")
    ap.add_argument("--source", help="확정본 CSV(학번,이름,세특). 안 주면 초안 폴더를 검사")
    ap.add_argument("--drafts", default="out/drafts_v3b", help="세특 초안이 든 폴더")
    ap.add_argument("--roster", default="out/roster.csv", help="명렬표(학번·이름)")
    ap.add_argument("--rules", default="draft-rules.json", help="길이·못 쓰는 말 규칙")
    ap.add_argument("-q", "--quiet", action="store_true",
                    help="'봐두실 것'은 안 보여주고 고쳐야 할 것만 보기")
    args = ap.parse_args()

    rules = load_rules(args.rules)
    recs = load_records(args)
    if not recs:
        sys.exit(f"{RED}검사 대상이 없다.{RESET}")

    keys = defaultdict(list)
    for hb, name, _ in recs:
        if k := parse_key(hb):
            keys[k].append(f"{hb} {name}")
        else:
            keys[("?", hb)].append(f"{hb} {name}")
    dup = {k: v for k, v in keys.items() if len(v) > 1}
    badhb = [hb for hb, _, _ in recs if not parse_key(hb)]

    results = [(hb, name, *check_text(txt, rules), neis_bytes(txt))
               for hb, name, txt in recs]
    failed = [r for r in results if r[2]]
    warned = [r for r in results if r[3] and not r[2]]
    sizes = sorted((r[4], r[0], r[1]) for r in results)

    bmax = rules.get("byte_max", 1500)
    print(f"{CYN}학생 {len(recs)}명 | 최대 길이 {bmax}바이트"
          f"(한글 약 {as_chars(bmax)}자){RESET}")
    print(f"  길이  가장 짧은 글 {as_chars(sizes[0][0])}자({sizes[0][1]} {sizes[0][2]}) · "
          f"평균 {as_chars(sum(s[0] for s in sizes) // len(sizes))}자 · "
          f"가장 긴 글 {as_chars(sizes[-1][0])}자({sizes[-1][1]} {sizes[-1][2]})")

    for k, v in dup.items():
        print(f"  {RED}❌ 같은 반·번호가 겹칩니다 {k[0]}반 {k[1]}번 ← {', '.join(v)}{RESET}")
    for hb in badhb:
        print(f"  {RED}❌ 학번이 5자리 숫자가 아닙니다: {hb!r}{RESET}")

    if failed:
        print(f"\n{RED}=== 고쳐야 할 학생 {len(failed)}명 ==={RESET}")
        for hb, name, hard, soft, nb in failed:
            print(f"  {RED}❌ {hb} {name}{RESET} (한글 약 {as_chars(nb)}자)")
            for tag, msg in hard:
                print(f"       [{tag}] {msg}")
            # 고칠 게 있는 학생일수록 볼 게 많다. 예전엔 이 사람들의 '봐두면 좋을 것'을
            # 통째로 버렸다(아래 warned 가 하드 실패자를 빼고 만들어지기 때문).
            for tag, msg in soft:
                print(f"       {DIM}⚠️ [{tag}] {msg} (안 고쳐도 됩니다){RESET}")

    if warned and not args.quiet:
        print(f"\n{YEL}=== 봐두시면 좋을 학생 {len(warned)}명 (안 고쳐도 됩니다) ==={RESET}")
        for hb, name, _, soft, nb in warned:
            print(f"  {YEL}⚠️ {hb} {name}{RESET} (한글 약 {as_chars(nb)}자) "
                  f"{DIM}{' / '.join(f'[{t}] {m}' for t, m in soft)}{RESET}")

    if failed or dup or badhb:
        sys.exit(f"\n{RED}검사에서 걸렸습니다 — 모두 "
                 f"{len(failed) + len(dup) + len(badhb)}건. 위 내용을 고쳐 주세요.{RESET}")
    print(f"\n{GRN}검사 통과 — {len(recs)}명 모두 이상 없습니다.{RESET}")


if __name__ == "__main__":
    main()
