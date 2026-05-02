#!/usr/bin/env python3
"""
NEIS 생기부 바이트 카운터.

학교생활기록부 기재요령 기준:
  - 한글 1자 = 3 byte
  - 영문/숫자/공백/일반 문장부호 = 1 byte
  - 그 외 (한자·일본어·이모지·특수기호 등) = 3 byte
  - 줄바꿈(\n) = 2 byte

사용법:
  python3 byte_count.py "측정할 문자열"
  echo "측정할 문자열" | python3 byte_count.py
  python3 byte_count.py --limit 1500 "문자열"   # 한도 비교 출력
"""

from __future__ import annotations

import argparse
import sys


def count_bytes(text: str) -> dict:
    hangul = 0
    ascii_chars = 0
    newline = 0
    other = 0
    for ch in text:
        code = ord(ch)
        if ch == "\n":
            newline += 1
        elif 0xAC00 <= code <= 0xD7A3:  # 한글 음절
            hangul += 1
        elif code < 128:  # ASCII (영문·숫자·공백·일반 문장부호)
            ascii_chars += 1
        else:  # 한자·이모지·특수기호 등
            other += 1

    neis = hangul * 3 + ascii_chars * 1 + other * 3 + newline * 2
    return {
        "char_total": len(text),
        "hangul": hangul,
        "ascii": ascii_chars,
        "other": other,
        "newline": newline,
        "neis_bytes": neis,
    }


def format_report(stats: dict, limit: int | None = None) -> str:
    lines = [
        f"총 글자수      : {stats['char_total']}",
        f"한글           : {stats['hangul']}자  ({stats['hangul'] * 3} byte)",
        f"ASCII          : {stats['ascii']}자  ({stats['ascii']} byte)",
        f"기타(한자/특수): {stats['other']}자  ({stats['other'] * 3} byte)",
        f"줄바꿈         : {stats['newline']}개  ({stats['newline'] * 2} byte)",
        f"NEIS 합계      : {stats['neis_bytes']} byte",
    ]
    if limit is not None:
        used = stats["neis_bytes"]
        pct = used / limit * 100
        remaining = limit - used
        status = "OK" if used <= limit else "OVER"
        lines.append(f"한도           : {limit} byte")
        lines.append(f"사용률         : {pct:.1f}%  (잔여 {remaining} byte)  [{status}]")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="NEIS 생기부 바이트 카운터")
    parser.add_argument("text", nargs="?", help="측정할 문자열 (생략 시 stdin)")
    parser.add_argument("--limit", type=int, default=None, help="바이트 한도(예: 1500)")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    text = args.text if args.text is not None else sys.stdin.read()
    stats = count_bytes(text)

    if args.json:
        import json

        payload = dict(stats)
        if args.limit is not None:
            payload["limit"] = args.limit
            payload["over_limit"] = stats["neis_bytes"] > args.limit
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(format_report(stats, args.limit))

    if args.limit is not None and stats["neis_bytes"] > args.limit:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
