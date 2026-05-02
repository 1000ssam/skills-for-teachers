#!/usr/bin/env python3
"""
output/세특_*.txt 파일들을 스캔하여 manifest.csv를 생성한다.

원칙:
  - 본문은 stdout으로 흘리지 않는다 (LLM 컨텍스트 보호).
  - stdout은 통계 요약 한두 줄만.
  - 결과 CSV는 사용자가 직접 열어 확인.

사용법:
  python3 merge_to_manifest.py <output_dir> <manifest_path> [--limit BYTES]

예:
  python3 merge_to_manifest.py output output/manifest.csv --limit 1500
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import sys
from pathlib import Path


def count_neis_bytes(text: str) -> int:
    hangul = sum(1 for c in text if 0xAC00 <= ord(c) <= 0xD7A3)
    ascii_chars = sum(1 for c in text if ord(c) < 128 and c != "\n")
    newline = text.count("\n")
    other = len(text) - hangul - ascii_chars - newline
    return hangul * 3 + ascii_chars + other * 3 + newline * 2


def extract_name(path: str) -> str:
    base = os.path.basename(path)
    name = base
    for prefix in ("세특_", "동아리_", "특기사항_"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    if name.endswith(".txt"):
        name = name[:-4]
    return name


def main() -> int:
    parser = argparse.ArgumentParser(description="생기부 결과 파일 → manifest.csv 통합")
    parser.add_argument("output_dir", help="학생별 .txt 파일이 있는 디렉터리")
    parser.add_argument("manifest_path", help="생성할 manifest CSV 경로")
    parser.add_argument("--limit", type=int, default=None, help="바이트 한도 (OVER 판정용)")
    parser.add_argument("--pattern", default="세특_*.txt", help="파일 글로브 패턴")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.is_dir():
        print(f"ERROR: '{output_dir}' is not a directory.", file=sys.stderr)
        return 2

    files = sorted(output_dir.glob(args.pattern))
    if not files:
        print(f"WARN: no files matched '{args.pattern}' in {output_dir}.", file=sys.stderr)
        return 1

    rows = []
    ok = over = empty = error = 0

    for path in files:
        name = extract_name(str(path))
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            rows.append({"name": name, "file": str(path), "bytes": 0, "status": "ERROR", "note": str(e)})
            error += 1
            continue

        if not text.strip():
            rows.append({"name": name, "file": str(path), "bytes": 0, "status": "EMPTY", "note": ""})
            empty += 1
            continue

        b = count_neis_bytes(text)
        if args.limit is not None and b > args.limit:
            status = "OVER"
            over += 1
        else:
            status = "OK"
            ok += 1
        rows.append({"name": name, "file": str(path), "bytes": b, "status": status, "note": ""})

    manifest_path = Path(args.manifest_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "file", "bytes", "status", "note"])
        writer.writeheader()
        writer.writerows(rows)

    # 요약 한두 줄. 본문은 절대 출력하지 않음.
    parts = [f"OK={ok}"]
    if args.limit is not None:
        parts.append(f"OVER={over}")
    parts.append(f"EMPTY={empty}")
    parts.append(f"ERROR={error}")
    print(f"Manifest written: {manifest_path} ({len(rows)} records, {' / '.join(parts)})")

    if over or error or empty:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
