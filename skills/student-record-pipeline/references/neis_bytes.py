#!/usr/bin/env python3
"""NEIS 생기부 바이트 카운터 (결정론적).

규칙(기재요령 2026 고등판 p.214 각주 공식 명시):
  - 한글·한자·전각문자 = 3 byte
  - 영문·숫자·공백·반각 문장부호(ASCII) = 1 byte
  - 개행(엔터) = 1 byte  (기재요령 원문: "엔터(Enter)는 1Byte")

과거 서드파티 계산기 중 엔터를 2로 세는 것도 있으나, 기재요령 공식 규정은 1이다.
필요 시 --newline-bytes로 변경 가능.

사용:
  echo "본문" | python3 neis_bytes.py
  python3 neis_bytes.py a.txt b.txt              # 파일별 바이트
  python3 neis_bytes.py out/ --max 650 --min 500 # 폴더 일괄 + 예산 판정
  python3 neis_bytes.py out/ --json              # 기계용 JSON
"""
import argparse
import json
import sys
from pathlib import Path


def neis_bytes(text: str, newline_bytes: int = 1) -> int:
    # \r\n → \n 정규화 후, 개행은 별도 가중치, 그 외는 ASCII=1 / 비ASCII=3
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    n = 0
    for ch in text:
        if ch == "\n":
            n += newline_bytes
        elif ord(ch) < 128:
            n += 1
        else:
            n += 3
    return n


def status(b: int, mn, mx) -> str:
    if mx is not None and b > mx:
        return f"OVER(+{b - mx})"
    if mn is not None and b < mn:
        return f"under(-{mn - b})"
    return "ok"


def iter_inputs(paths):
    """파일/폴더/stdin을 (라벨, 텍스트) 스트림으로."""
    if not paths:
        yield ("<stdin>", sys.stdin.read())
        return
    for p in paths:
        path = Path(p)
        if path.is_dir():
            for f in sorted(path.rglob("*.txt")):
                yield (str(f), f.read_text(encoding="utf-8", errors="replace"))
        else:
            yield (str(path), path.read_text(encoding="utf-8", errors="replace"))


def main():
    ap = argparse.ArgumentParser(description="NEIS 생기부 바이트 카운터")
    ap.add_argument("paths", nargs="*", help="텍스트 파일/폴더 (없으면 stdin)")
    ap.add_argument("--newline-bytes", type=int, default=1, help="개행 1자 바이트(기재요령 공식=1)")
    ap.add_argument("--max", type=int, default=None, help="상한(초과 시 OVER)")
    ap.add_argument("--min", type=int, default=None, help="하한(미만 시 under, 참고용)")
    ap.add_argument("--json", action="store_true", help="JSON 출력")
    args = ap.parse_args()

    rows = []
    for label, text in iter_inputs(args.paths):
        b = neis_bytes(text, args.newline_bytes)
        rows.append({"label": label, "bytes": b, "status": status(b, args.min, args.max)})

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            tag = "" if r["status"] == "ok" else f"  [{r['status']}]"
            print(f"{r['bytes']:>5}  {r['label']}{tag}")


if __name__ == "__main__":
    main()
