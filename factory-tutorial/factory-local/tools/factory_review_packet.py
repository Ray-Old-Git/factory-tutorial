#!/usr/bin/env python3
"""factory_review_packet — build a concise, redacted diff + summary for the
online reviewer.

Usage:
    python3 tools/factory_review_packet.py [--project-dir DIR] [--task "..."]
        [--base REF] [--questions "q1,q2"] [--limitations "..."]
        [--verify-json FILE] [--out-dir DIR] [--max-diff-lines N]

The packet at <out-dir>/packet-<id>.md contains:
  - Task
  - Diff since --base (default: commit stored in checkpoint.json, else HEAD~1),
    bounded to --max-diff-lines (default 4000)
  - Local verify summary from --verify-json
  - Known limitations
  - Review questions
Secrets are redacted with a pattern list (passwords, tokens, keys, ...).
Prints: the packet path.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_MAX_DIFF_LINES = 4000

REDACTIONS = [
    (re.compile(
        r"(?i)\b(password|passwd|secret|token|api[_-]?key|authorization|credential)\b(\s*[=:]\s*)([^\s&\"']+)"),
     r"\1\2[REDACTED]"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]+"), "Bearer [REDACTED]"),
]


def redact(text: str) -> str:
    for pattern, repl in REDACTIONS:
        text = pattern.sub(repl, text)
    return text


def _git(args, cwd):
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True
        ).stdout.strip()
    except FileNotFoundError:
        return ""


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a redacted review packet.")
    ap.add_argument("--project-dir", default=".", help="project folder (default: cwd)")
    ap.add_argument("--task", default="", help="the milestone/feature description")
    ap.add_argument("--base", default="", help="git ref to diff from")
    ap.add_argument("--questions", default="", help="comma-separated review questions")
    ap.add_argument("--limitations", default="", help="known limitations")
    ap.add_argument("--verify-json", default="", help="path to factory_verify JSON")
    ap.add_argument("--out-dir", default="", help="output dir (default: <project>/review)")
    ap.add_argument("--max-diff-lines", type=int, default=DEFAULT_MAX_DIFF_LINES)
    args = ap.parse_args()

    proj = Path(args.project_dir).resolve()
    cp = _read_json(proj / "checkpoint.json") or {}
    now = dt.datetime.now().astimezone()
    cp_id = cp.get("id") or now.strftime("%Y%m%d-%H%M")

    out_dir = Path(args.out_dir).resolve() if args.out_dir else proj / "review"
    out_dir.mkdir(parents=True, exist_ok=True)
    packet_path = out_dir / f"packet-{cp_id}.md"

    base = args.base
    if not base and cp.get("commit"):
        base = cp["commit"]
    elif not base:
        base = "HEAD~1"

    if _git(["rev-parse", "--is-inside-work-tree"], proj) == "true":
        stat = _git(["diff", "--stat", base, "HEAD"], proj).strip()
        diff = _git(["diff", base, "--", "."], proj)
    else:
        stat = ""
        diff = "no git repo — no diff available"

    diff = redact(diff or "")
    lines = diff.splitlines()
    if len(lines) > args.max_diff_lines:
        diff = "\n".join(lines[: args.max_diff_lines]) + (
            f"\n... [truncated: {len(lines) - args.max_diff_lines} more lines]"
        )

    questions = [q.strip() for q in args.questions.split(",") if q.strip()]

    verify = _read_json(Path(args.verify_json)) if args.verify_json else None
    if verify:
        checks = verify.get("checks", [])
        passed = sum(1 for c in checks if c.get("passed"))
        verify_text = f"ok={verify.get('ok')} ({passed}/{len(checks)} checks passed)"
    else:
        verify_text = "(not run)"

    parts = [
        f"# Review packet — {cp_id}",
        f"- Generated: {now.isoformat(timespec='seconds')}",
        f"- Task: {args.task or '(unspecified)'}",
        f"- Base ref: {base}",
        "",
        "## Local verify",
        verify_text,
        "",
        "## Diff stat",
        stat or "(none)",
        "",
        "## Diff",
        "```diff",
        diff,
        "```",
        "",
        "## Known limitations",
        args.limitations or "(none provided)",
        "",
        "## Review questions",
    ]
    if questions:
        parts.extend(f"- {q}" for q in questions)
    else:
        parts.append("(none provided)")

    packet_path.write_text("\n".join(parts) + "\n")
    print(packet_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
