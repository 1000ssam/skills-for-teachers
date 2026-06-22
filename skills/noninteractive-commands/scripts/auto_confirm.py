#!/usr/bin/env python3
"""Run a command with bounded answers supplied on stdin."""

from __future__ import annotations

import argparse
import subprocess
import sys


RISKY_PATTERNS = (
    "rm ",
    "remove-item",
    " del ",
    " erase ",
    " rmdir ",
    " rd ",
    "git reset",
    "git clean",
    "git push --force",
    "git push -f",
    "drop database",
    "drop table",
    "truncate table",
    "format ",
    "diskpart",
    "winget uninstall",
    "choco uninstall",
    "scoop uninstall",
    "npm uninstall",
    "pip uninstall",
    "kubectl delete",
    "terraform destroy",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Supply a bounded number of stdin answers to a command."
    )
    parser.add_argument("--answer", default="y", help="Answer to send each time.")
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="Number of answer lines to send. Default: 1.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120,
        help="Timeout in seconds. Default: 120.",
    )
    parser.add_argument(
        "--allow-risky",
        action="store_true",
        help="Allow commands matching destructive-pattern guards.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command and answers without running it.",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    if args.command and args.command[0] == "--":
        args.command = args.command[1:]

    if not args.command:
        parser.error("provide a command after --")
    if args.repeat < 1 or args.repeat > 20:
        parser.error("--repeat must be between 1 and 20")
    if "\0" in args.answer:
        parser.error("--answer cannot contain NUL")
    if len(args.answer) > 100:
        parser.error("--answer is too long")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return args


def looks_risky(command: list[str]) -> str | None:
    joined = f" {' '.join(command).lower()} "
    for pattern in RISKY_PATTERNS:
        if pattern in joined:
            return pattern.strip()
    return None


def main() -> int:
    args = parse_args()
    risky = looks_risky(args.command)
    if risky and not args.allow_risky:
        print(
            f"Refusing to auto-confirm command matching risky pattern: {risky}",
            file=sys.stderr,
        )
        print(
            "Use --allow-risky only after the user explicitly confirms the exact action and target.",
            file=sys.stderr,
        )
        return 2

    payload = "".join(f"{args.answer}\n" for _ in range(args.repeat))
    if args.dry_run:
        print("Command:", " ".join(args.command))
        print("Answer:", repr(args.answer))
        print("Repeat:", args.repeat)
        return 0

    try:
        completed = subprocess.run(
            args.command,
            input=payload,
            text=True,
            timeout=args.timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {args.timeout:g}s", file=sys.stderr)
        return 124
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 127

    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
