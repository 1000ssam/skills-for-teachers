#!/usr/bin/env python3
"""설정이 다 채워졌는지 본다 — **빈칸이면 멈춘다.**

왜 이 파일이 있나:
  이 스킬의 설정 파일들은 '예시'와 '시작 파일'이 같은 파일이었다. 예시는 채워져 있어야
  쓸모가 있고 시작 파일은 비어 있어야 안전한데, 한 파일이 두 일을 했다. 그래서 **이전
  과목의 값이 그대로 남은 채로, 아무 에러 없이, 그럴듯한 결과**가 나왔다.

  실제로 그렇게 터진 것들(2026-08-03 실측):
    · scan_pattern 기본값(손글씨용)이 `20501_p1.txt` 의 `1` 을 스캔 연번으로 읽어 **반 전원 한 칸씩 밀림**
    · sections.json 이 이전 과제의 2칸(p3·p4)인 채라 학생이 **'원문 없음'으로 조용히 빠짐**
    · draft-rules.json 의 forbidden 이 빈 목록이라 **'교내대회 수상'이 검사 통과**
    · build_students.py 가 기본 반 "5" 로 **0명 조립하고 "완료"**
    · 계약서의 «BYTE_MAX» 를 안 채워 **그 글자가 그대로 모델에게 전달**

  전부 "에러를 안 내고 그럴듯하게 진행"이 공통점이다. 그래서 여기서 **막는다.**

쓰는 법:
  python3 tool/check_config.py            # 검사만 (통과=0 / 걸림=1)
  python3 tool/check_config.py --fix      # 결정론으로 채울 수 있는 건 채운다(계약서 자리표시자)
"""
import argparse, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tool")
RED, YEL, GRN, DIM, RESET = "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"

# 예시 파일에 박혀 있던 값들. 이게 그대로 남아 있으면 "안 채운 것"이다.
TEMPLATE_MARKS = {
    "scan_pattern": [r"(\d+)\s*\.txt$"],
    "section_label": ["칸 제목을 바꾸세요"],
    "contract_placeholder": ["«BYTE_MAX»", "«FORBIDDEN»", "«SOFT»"],
    "contract_fewshot": ["여기부터 교사 정본을 붙여넣는다"],
}

problems, warns = [], []


def bad(what, why, how):
    problems.append((what, why, how))


def warn(what, why):
    warns.append((what, why))


def jload(p):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception as e:
        return {"__error__": str(e)}


def check_mapping():
    p = os.path.join(ROOT, "mapping-config.json")
    if not os.path.exists(p):
        return warn("mapping-config.json", "없습니다 — 아직 ③ 누구 글인지 맞추기를 안 하셨다면 정상입니다")
    c = jload(p)
    if "__error__" in c:
        return bad("mapping-config.json", f"읽을 수 없습니다({c['__error__']})", "JSON 형식을 고쳐 주세요")
    sp = c.get("scan_pattern", "")
    if sp in TEMPLATE_MARKS["scan_pattern"]:
        bad("mapping-config.json → scan_pattern", "예시 기본값 그대로입니다(손글씨 스캔용)",
            "학생 글이 디지털 제출(파일명에 학번)이면 이 패턴에 **안 걸리는** 값으로 바꾸세요.\n"
            '       예: "^scan[-_](\\\\d+)\\\\.txt$"   ← 그래야 파일명=학번으로 정박합니다.\n'
            "       그대로 두면 20501_p1.txt 의 '1' 을 연번으로 읽어 반 전원이 한 칸씩 밀립니다.")
    if not (c.get("boilerplate") or []):
        bad("mapping-config.json → boilerplate", "비어 있습니다",
            "인쇄된 양식 문구를 못 걷어내면 **백지가 백지로 안 보입니다**(칸 이름이 글자로 잡힘).")


def check_sections():
    p = os.path.join(ROOT, "sections.json")
    if not os.path.exists(p):
        return bad("sections.json", "없습니다", "활동지 칸 구성을 적어 주세요.")
    c = jload(p)
    secs = c.get("sections", c) if isinstance(c, dict) else c
    if not secs:
        return bad("sections.json", "칸이 하나도 없습니다", "활동지 칸을 적어 주세요.")
    for s in secs:
        for mark in TEMPLATE_MARKS["section_label"]:
            if mark in (s.get("label") or ""):
                bad("sections.json", f"칸 제목이 예시 그대로입니다('{s.get('label')}')",
                    "활동지 실제 칸 이름으로 바꾸세요. 안 맞으면 학생이 '원문 없음'으로 조용히 빠집니다.")


def check_rules():
    p = os.path.join(ROOT, "draft-rules.json")
    if not os.path.exists(p):
        return bad("draft-rules.json", "없습니다", "길이 상한을 적어 주세요.")
    c = jload(p)
    if not c.get("byte_max"):
        bad("draft-rules.json → byte_max", "비어 있습니다", "길이 상한(바이트)을 적어 주세요.")
    # forbidden 이 비는 건 **정상**이다 — 기재요령 금지어는 gate.py 가 따로 항상 읽는다.
    gp = [os.path.join(TOOL, "forbidden-terms.txt"),
          os.path.join(os.path.expanduser("~/.claude/skills/student-record-pipeline"),
                       "references", "forbidden-terms.txt")]
    if not any(os.path.exists(x) for x in gp):
        bad("forbidden-terms.txt", "기재요령 금지어 목록을 못 찾습니다",
            "이게 없으면 '수상·TOEIC' 같은 말이 검사를 그냥 통과합니다.")


def check_contract(fix=False):
    p = os.path.join(TOOL, "render_contract.md")
    if not os.path.exists(p):
        return bad("tool/render_contract.md", "없습니다", "세특을 어떤 틀로 쓸지 적어 주세요.")
    s = open(p, encoding="utf-8").read()

    # 자리표시자는 «BYTE_MAX» 처럼 딱 떨어지기도 하고 «FORBIDDEN — 설명…» 처럼 설명이 붙기도 한다.
    # 이름만 비교하면 후자를 놓친다 — 남아 있는 «…» 를 통째로 찾는다.
    left = re.findall(r"«[^»]*»", s)
    if left and fix:
        r = jload(os.path.join(ROOT, "draft-rules.json"))
        s = s.replace("«BYTE_MAX»", str(r.get("byte_max", 1500)))
        s = s.replace("«FORBIDDEN — 없으면 이 줄을 통째로 지운다»",
                      ", ".join(r.get("forbidden") or []) or "(이 과제 전용 금지어 없음)")
        s = s.replace("«FORBIDDEN»", ", ".join(r.get("forbidden") or []) or "(없음)")
        s = s.replace("«SOFT»", ", ".join(r.get("soft") or []) or "(없음)")
        open(p, "w", encoding="utf-8").write(s)
        print(f"{GRN}  ✔ 계약서 자리표시자를 draft-rules.json 값으로 채웠습니다: {', '.join(left)}{RESET}")
        left = re.findall(r"«[^»]*»", s)
    if left:
        short = [m if len(m) < 24 else m[:22] + "…»" for m in dict.fromkeys(left)]
        bad("tool/render_contract.md", f"채워야 할 자리가 남아 있습니다: {', '.join(short)}",
            "`python3 tool/check_config.py --fix` 를 돌리면 draft-rules.json 값으로 채웁니다.\n"
            "       그대로 두면 그 글자가 **모델에게 그대로 전달**됩니다.")

    # §3 퓨샷이 비었는지. '[교사 정본]' 은 §3 위쪽 **작성 요령**에도 나오므로 그걸로 세면 안 된다.
    # 붙여넣기 자리(주석) **뒤쪽**만 잘라서 본다.
    for mark in TEMPLATE_MARKS["contract_fewshot"]:
        i = s.find(mark)
        if i < 0:
            continue
        tail = s[i:]
        tail = tail.split("\n## ", 1)[0]          # 다음 절(§4 출력) 전까지
        if "[교사 정본" not in tail:
            bad("tool/render_contract.md → §3 퓨샷", "교사 정본이 비어 있습니다",
                "선생님이 쓰신 세특 3~4편을 넣으세요. 비면 문체의 출처가 없어\n"
                "       전원이 AI 기본 문투로 나옵니다.")
        break


def check_context():
    p = os.path.join(ROOT, "out", "marks", "_context.json")
    ctx = (jload(p).get("context") or "").strip() if os.path.exists(p) else ""
    if not ctx:
        warn("활동 맥락(out/marks/_context.json)",
             "비어 있습니다 — 모든 세특의 첫 문장이 빠진 채로 나옵니다. 화면 왼쪽 맨 위에서 적으실 수 있습니다")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true", help="결정론으로 채울 수 있는 것을 채운다")
    a = ap.parse_args()

    check_mapping(); check_sections(); check_rules(); check_contract(a.fix); check_context()

    for what, why in warns:
        print(f"{YEL}⚠️ {what}{RESET} — {why}")
    if not problems:
        print(f"{GRN}설정 검사 통과 — 다 채워져 있습니다.{RESET}")
        return 0
    print(f"\n{RED}설정이 덜 채워졌습니다 ({len(problems)}건). 이대로 쓰면 조용히 틀립니다.{RESET}\n")
    for what, why, how in problems:
        print(f"{RED}  ✗ {what}{RESET}\n     {why}\n     {DIM}→ {how}{RESET}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
