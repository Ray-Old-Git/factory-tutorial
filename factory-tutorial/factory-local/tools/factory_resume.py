#!/usr/bin/env python3
"""factory_resume — startup inspection for resuming the factory session.

Prints:
  - HANDOFF.md (the human-readable resume sheet), if present
  - checkpoint.json, if present
  - `git log --oneline -10`, if the project is a git repo
  - `git status --porcelain` (uncommitted files), if a repo
  - `backups/` contents, if any

WARNING lines are printed when the state looks inconsistent or incomplete:
  - no HANDOFF.md yet
  - last checkpoint status is "done" but the last verify did not pass
  - last checkpoint status is "in-progress" but the last verify did not pass

Exit code: 0 when clean, 1 when warnings were printed.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _git(args, cwd):
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True
        ).stdout.strip()
    except FileNotFoundError:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Inspect factory state and print the resume sheet.")
    ap.add_argument("--project-dir", default=".", help="project folder (default: cwd)")
    args = ap.parse_args()
    proj = Path(args.project_dir).resolve()

    handoff = proj / "HANDOFF.md"
    print("===== HANDOFF.md =====")
    if handoff.exists():
        print(handoff.read_text())
    else:
        print("(none — the factory has not written a handoff yet)")

    cp = _read_json(proj / "checkpoint.json")
    print("===== checkpoint.json =====")
    print(json.dumps(cp, indent=2) if cp else "(none)")

    # Open and in-progress tasks
    tasks = _read_json(proj / "tasks.json") or {}
    print("===== tasks =====")
    if isinstance(tasks, dict) and tasks.get("tasks"):
        for t in tasks["tasks"]:
            print(f"- #{t.get('id')} [{t.get('status')}] {t.get('text')}")
    else:
        print("(none)")

    if _git(["rev-parse", "--is-inside-work-tree"], proj) == "true":
        print("===== git log =====")
        print(_git(["log", "--oneline", "-10"], proj) or "(empty)")
        print("HEAD:", _git(["rev-parse", "--short", "HEAD"], proj))
        print("===== git status =====")
        print(_git(["status", "--porcelain"], proj) or "(clean)")

    backups = proj / "backups"
    if backups.is_dir():
        names = sorted(p.name for p in backups.glob("*.tar.gz"))
        print("===== backups =====")
        print("\n".join(names) if names else "(empty)")

    warnings = []
    if not handoff.exists():
        warnings.append("no HANDOFF.md found — starting from scratch?")
    if cp:
        verify = cp.get("verify") or {}
        status = cp.get("status")
        if status == "done" and not verify.get("ok"):
            warnings.append("last checkpoint says 'done' but the last verify did not pass")
        if status == "in-progress" and not verify.get("ok"):
            warnings.append("last checkpoint says 'in-progress' but the last verify did not pass")

    if warnings:
        print("===== WARNINGS =====")
        for w in warnings:
            print("- " + w)

    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
