#!/usr/bin/env python3
"""이제 씁니다 — 지금 상태를 보여주고, **새로 써야 할 사람만** 골라 배치를 준비한다.

왜 이 파일이 있나:
  실시간 감시(watch.sh)를 걷어내고 '선생님이 다 표시한 뒤 한 번 부르는' 방식으로 바꾸면서,
  **여러 번 나눠 부르는 일**이 기본이 됐다(3명 먼저 보고 → 나머지 → 반려분 다시).
  그때마다 "이미 다 쓴 사람을 또 쓰는" 사고가 나면 안 된다. 이 파일이 그 경계를 지킨다.

  판정 규칙은 pending.py 를 **그대로 가져다 쓴다**(복제 금지 — 두 벌이 되면 반드시 갈린다).

쓰는 법:
  python3 tool/render_now.py                 # 상태표 + 새로/다시 쓸 사람만 준비
  python3 tool/render_now.py --status        # 표만 보고 끝 (아무것도 준비 안 함)
  python3 tool/render_now.py --opus          # 재작성용 Opus 라인으로 준비
  python3 tool/render_now.py --all           # 확정·보류 뺀 전원을 다시 쓴다(주의)
  python3 tool/render_now.py 20501 20503     # 지정한 사람만
"""
import os, sys, json, glob, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, "tool")
MARKS = os.path.join(ROOT, "out", "marks")
DRAFTS = os.path.join(ROOT, "out", "drafts_v3b")
sys.path.insert(0, TOOL)
from pending import material_ms          # 단일 출처: 재료 최신성 판정

SK = os.path.join(os.path.expanduser("~/.claude/skills/student-record-pipeline"), "references")
if os.path.isdir(SK):
    sys.path.insert(0, SK)
try:
    from neis_bytes import neis_bytes
except Exception:
    def neis_bytes(t):                    # 스킬이 없으면 바이트는 생략한다(판정에는 안 쓴다)
        return sum(1 if ord(c) < 128 else 3 for c in t)


# ── 상태 ─────────────────────────────────────────────────────────────────────
# 쓸 것 / 안 쓸 것을 이 표 하나로 가른다. 라벨은 선생님이 읽는 말이다(헌법 9).
WRITE = "📝 처음 씀", "🔁 다시 씀"
LABEL_HELP = {
    "✅ 확정":        "선생님이 확정하셨습니다. 건드리지 않습니다.",
    "⏸ 보류":        "선생님이 판정을 미루셨습니다. 건드리지 않습니다.",
    "✔ 이미 씀":      "초안이 이미 있고 그 뒤로 표시가 바뀌지 않았습니다. 다시 쓰지 않습니다.",
    "📝 처음 씀":     "아직 초안이 없습니다. 이번에 씁니다.",
    "🔁 다시 씀":     "표시를 고치셨거나 [다시]를 누르셨습니다. 이번에 다시 씁니다.",
    "⬜ 마킹 안 끝남": "'마킹 끝'을 아직 안 누르셨습니다. 이번 대상이 아닙니다.",
    "⛔ 원문 없음":    "낸 글이 없습니다. 이번 대상이 아닙니다.",
}


def wide(t):
    """터미널 표시 폭. 한글·전각은 두 칸을 차지한다 — 안 세면 표가 어긋난다."""
    return sum(2 if ord(c) > 0x1100 else 1 for c in str(t))


def pad(t, n):
    return str(t) + " " * max(0, n - wide(t))


def load_students():
    p = os.path.join(TOOL, "students.json")
    d = json.load(open(p, encoding="utf-8"))
    secs = [s["key"] for s in d["sections"]]
    return d["students"], secs


def material_grade():
    """매핑 단계가 이미 잰 '재료' 판정(백지/한칸결손/정상)을 그대로 쓴다.

    학생 글 문자열 길이로 백지를 다시 재면 인쇄된 칸 이름([1-1 …])이 글자로 잡혀
    백지가 백지로 안 보인다. 그 계산은 map_pages.py 가 boilerplate 를 걷어내고
    이미 해 뒀으므로 여기서 다시 하지 않는다(로직 복제 금지).
    """
    import csv
    p = os.path.join(ROOT, "out", "mapping_reconciled.csv")
    if not os.path.exists(p):
        return {}
    try:
        return {r["학번"].strip(): (r.get("재료") or "").strip()
                for r in csv.DictReader(open(p, encoding="utf-8-sig"))}
    except Exception:
        return {}


def classify(s, secs, grade):
    """이 학생을 이번에 쓸 것인가. (상태, 초안바이트, 반려횟수)"""
    hk = s["hakbun"]
    mp = os.path.join(MARKS, f"{hk}.json")
    dp = os.path.join(DRAFTS, f"{hk}.json")

    draft_b, rj = None, 0
    if os.path.exists(dp):
        try:
            draft_b = neis_bytes(json.load(open(dp, encoding="utf-8")).get("setuk", ""))
        except Exception:
            draft_b = None

    # 백지는 매핑 단계 판정을 따른다. 여기서 다시 세면 인쇄된 칸 이름에 속는다.
    if grade.get(hk) in ("백지", "OCR붕괴"):
        return "⛔ 원문 없음", draft_b, rj
    if not any((s.get(k) or "").strip() for k in secs):
        return "⛔ 원문 없음", draft_b, rj
    if not os.path.exists(mp):
        return "⬜ 마킹 안 끝남", draft_b, rj
    try:
        m = json.load(open(mp, encoding="utf-8"))
    except Exception:
        return "⬜ 마킹 안 끝남", draft_b, rj

    rj = len(m.get("rejects") or [])
    if m.get("approved"): return "✅ 확정", draft_b, rj
    if m.get("held"):     return "⏸ 보류", draft_b, rj
    if not m.get("done"): return "⬜ 마킹 안 끝남", draft_b, rj
    if not os.path.exists(dp):
        return "📝 처음 씀", draft_b, rj
    if material_ms(m, mp) > os.path.getmtime(dp) * 1000:
        return "🔁 다시 씀", draft_b, rj
    return "✔ 이미 씀", draft_b, rj


def main():
    argv = sys.argv[1:]
    status_only = "--status" in argv;  argv = [a for a in argv if a != "--status"]
    force_all   = "--all" in argv;     argv = [a for a in argv if a != "--all"]
    use_opus    = "--opus" in argv;    argv = [a for a in argv if a != "--opus"]
    only = [a for a in argv if not a.startswith("-")]

    students, secs = load_students()
    grade = material_grade()
    rows = [(s, *classify(s, secs, grade)) for s in students]

    w = max(wide(s["name"]) for s, *_ in rows) + 2
    print("\n " + pad("반", 5) + pad("학번", 8) + pad("이름", w)
          + pad("상태", 16) + pad("초안", 8) + "다시")
    print("─" * (37 + w))
    for s, st, b, rj in rows:
        print(" " + pad(s["cls"], 5) + pad(s["hakbun"], 8) + pad(s["name"], w)
              + pad(st, 16) + pad(f"{b}B" if b else "—", 8)
              + (f"{rj}회" if rj else ""))

    counts = {}
    for _, st, _, _ in rows:
        counts[st] = counts.get(st, 0) + 1
    print("─" * (37 + w))
    for st, n in sorted(counts.items()):
        print(f"  {st}  {n}명   — {LABEL_HELP.get(st,'')}")

    # ── 이번에 쓸 사람 ────────────────────────────────────────────────────────
    if only:
        targets = [s["hakbun"] for s, st, _, _ in rows if s["hakbun"] in only]
        missing = [h for h in only if h not in targets]
        if missing:
            print(f"\n❌ 명렬표에 없는 학번: {' '.join(missing)}", file=sys.stderr)
            sys.exit(2)
        why = "지정하신 사람만"
    elif force_all:
        targets = [s["hakbun"] for s, st, _, _ in rows
                   if st not in ("✅ 확정", "⏸ 보류", "⬜ 마킹 안 끝남", "⛔ 원문 없음")]
        why = "--all — 확정·보류를 뺀 전원 (이미 쓴 것도 덮어씁니다)"
    else:
        targets = [s["hakbun"] for s, st, _, _ in rows if st in WRITE]
        why = "새로 쓰거나 다시 써야 하는 사람만"

    print(f"\n▶ 이번에 쓸 사람: {len(targets)}명 ({why})")
    if targets:
        print("  " + " ".join(targets))
    kept = [s["hakbun"] for s, st, _, _ in rows if st == "✔ 이미 씀"]
    if kept and not force_all:
        print(f"  (이미 쓴 {len(kept)}명은 그대로 둡니다: {' '.join(kept)})")

    # ── 활동 맥락 게이트 ──────────────────────────────────────────────────────
    # 맥락은 모든 세특의 첫 문장이다. 비어 있으면 "○○ 활동에서" 가 통째로 빠진 채 나가고,
    # 그건 다 쓴 뒤에야 보인다(실측 2026-08-03 — 3명분을 그렇게 버렸다).
    # 판정은 하되 막지는 않는다. 무엇을 쓸지는 선생님이 정하신다.
    ctx = ""
    cp = os.path.join(MARKS, "_context.json")
    if os.path.exists(cp):
        try:
            ctx = (json.load(open(cp, encoding="utf-8")).get("context") or "").strip()
        except Exception:
            ctx = ""
    if ctx:
        print(f"\n활동 맥락: {ctx[:60]}{'…' if len(ctx) > 60 else ''}")
    else:
        print("\n⚠️ 활동 맥락이 비어 있습니다 — 모든 세특의 첫 문장이 빠진 채로 나옵니다.")
        print("   화면 왼쪽 맨 위 '① 활동 맥락' 에 한 줄 적으신 뒤 다시 부르시길 권합니다.")
        print("   (그냥 진행하셔도 됩니다. 나중에 채우고 다시 쓰면 그 사람들만 다시 씁니다.)")

    if status_only:
        return
    if not targets:
        print("\n쓸 사람이 없습니다. 표시를 더 하셨거나 [다시]를 누르신 뒤 다시 부르세요.")
        return

    # ── 설정 게이트 ──────────────────────────────────────────────────────────
    # 예시 기본값이 그대로 남은 채 렌더하면 조용히 틀린 결과가 나온다(→ check_config.py).
    # 여기서 막는 게 유일하게 값싼 지점이다 — 렌더가 돌기 시작하면 되돌리는 데 돈이 든다.
    sys.stdout.flush()   # 안 흘리면 아래 하위 프로세스 출력이 위 표보다 먼저 찍혀 순서가 엉킨다
    rc = subprocess.run([sys.executable, os.path.join(TOOL, "check_config.py")]).returncode
    if rc != 0:
        print("\n설정을 먼저 채워 주세요. 채운 뒤 다시 부르시면 됩니다.", file=sys.stderr)
        sys.exit(rc)

    batch = "batch_render_opus.js" if use_opus else "batch_render_sonnet.js"
    cmd = [sys.executable, os.path.join(TOOL, "build_run_batch.py"), "--batch", batch, *targets]
    print(f"\n── 배치 준비 ({batch}) ──")
    sys.exit(subprocess.run(cmd).returncode)


if __name__ == "__main__":
    main()
