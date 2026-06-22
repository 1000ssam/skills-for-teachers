---
name: noninteractive-commands
description: Use when the user asks Codex to avoid pressing y/yes/enter, auto-handle confirmation prompts, or run terminal commands noninteractively, including Korean-language equivalents. Prefer explicit flags and scoped environment variables without bypassing Codex approval UI or destructive confirmations.
---

# Noninteractive Commands

## Overview

Make terminal work noninteractive where it is safe. Treat requests to press `y`, `yes`, `Enter`, `A`, "all", "OK", "confirm", "accept", "continue", "agree", "approve", or "do not ask" as requests to remove avoidable prompts, not as permission to blindly confirm every prompt.

## Boundaries

- Do not automate or bypass Codex's own approval UI, trust prompts, or safety prompts. If repeated prompts appear to come from Codex itself, inspect `~/.codex/config.toml`, active profiles, and `codex --help`, then report the relevant setting or launch flag.
- Do not use broad `yes | <command>` or equivalent endless confirmation streams by default.
- Do not treat a generic "press y/yes for me" request as consent for destructive or irreversible actions: deletion, overwrite, package removal, disk or partition changes, database migrations, force push, reset/checkout, production deploys, credential changes, permission broadening, purchases, or billing changes.
- For destructive actions, require an explicit user request for the exact action and target in the current task before using any confirmation-suppressing flag.
- Prefer native noninteractive flags over simulated input. Use simulated input only when the prompt is narrow, deterministic, low-risk, and no native flag exists.
- If a prompt asks for a decision that changes scope, cost, data loss, security, or production state, stop and ask the user.

## Workflow

1. Identify the source of the prompt: Codex UI, shell command, package manager, scaffolder, installer, test runner, or custom script.
2. Prefer a documented noninteractive option: `--yes`, `--yes=true`, `--no-interactive`, `--ci`, `--defaults`, `--accept-*`, `-y`, `-Confirm:$false`, or an answers/config file.
3. For generators, prefer explicit options that encode the choice instead of accepting defaults blindly.
4. For package managers and test/build tools, set narrowly scoped environment variables only for the command that needs them.
5. Use `--force` only when the tool documents it as non-destructive for the current target.
6. If a command still blocks, rerun only after choosing a safer flag or explain why confirmation is needed.
7. Tell the user when a prompt cannot be safely removed.

## Bounded Auto-Confirm

When no native noninteractive flag exists and the prompt is narrow, deterministic, inspected, and low-risk, use the bundled script instead of an endless `yes` stream:

```powershell
python C:\Users\hserver\.codex\skills\noninteractive-commands\scripts\auto_confirm.py --answer y --repeat 1 -- <command> <args>
```

Use `--repeat` only for a known number of prompts. The script refuses common destructive command patterns unless `--allow-risky` is supplied; use that override only after the user explicitly confirms the exact action and target in the current task.

## Common Patterns

Use these as starting points and verify with each command's help output when uncertain:

- Codex CLI: use `codex -a never -s danger-full-access` only in a trusted workspace, or persist equivalent settings in `~/.codex/config.toml`. Do not recommend `--dangerously-bypass-approvals-and-sandbox` unless the user explicitly accepts the risk and the environment is externally sandboxed.
- PowerShell: use command-specific parameters such as `-Confirm:$false` only after the target scope is explicit and inspected. Avoid global `$ConfirmPreference = 'None'` except inside a tightly scoped script block.
- npm: use `npm init -y`, `npm create <pkg>@latest -- --yes` when supported, or pass explicit template flags. Use `CI=1` only for tools that document CI behavior.
- pnpm/yarn: use documented `--yes`, `--defaults`, or template flags when available.
- pip/uv/poetry: use `--yes`, `--no-input`, or equivalent documented flags when available.
- winget: use `--accept-source-agreements` and `--accept-package-agreements` for trusted packages.
- choco/scoop: use `-y` or documented noninteractive flags for trusted packages.
- git: avoid auto-confirming history-rewriting or destructive commands. Prefer explicit noninteractive commands only for read-only or clearly scoped operations.

## Simulated Input

Use simulated input only as a last resort:

- The prompt text and accepted response are known.
- The action is reversible or low-impact.
- The command target was inspected.
- The simulated response is bounded, for example a single `y` or newline, not an endless stream.
