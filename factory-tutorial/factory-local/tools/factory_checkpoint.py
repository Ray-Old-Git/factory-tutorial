#!/usr/bin/env python3
"""factory_checkpoint — snapshot the project and append a checkpoint entry.

Usage:
    python3 tools/factory_checkpoint.py [--project-dir DIR] [--task "..."]
        [--status STATUS] [--notes "..."] [--verify-json FILE]

Actions:
  1. If the project is a git repo: `git add -A` + `git commit --allow-empty`
     (every checkpoint gets a commit id). Otherwise: write a timestamped
     tarball into backups/.
  2. Append a timestamped entry to HANDOFF.md.
  3. Write checkpoint.json (id, time, task, status, verify summary, commit id,
     diff stat, dirty files).

With `--require-ok`, the checkpoint is refused (exit 1) when the verify JSON
(from `--verify-json`, or the newest file in `verify_runs/`) says ok != True;
exit 2 when there is no verify run at all.

Prints: the checkpoint id.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import secrets
import subprocess
import sys
import tarfile
from pathlib import Path


def _git(args, cwd):
    try:
        return subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True
        ).stdout
    except FileNotFoundError:
        return ""


def _is_repo(proj: Path) -> bool:
    return _git(["rev-parse", "--is-inside-work-tree"], proj).strip() == "true"


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Snapshot the project and append a checkpoint entry.")
    ap.add_argument("--project-dir", default=".", help="project folder (default: cwd)")
    ap.add_argument("--task", default="", help="what was done")
    ap.add_argument("--status", default="checkpoint", help="e.g. done, in-progress, blocked")
    ap.add_argument("--notes", default="")
    ap.add_argument("--verify-json", default="", help="path to factory_verify JSON output")
    ap.add_argument(
        "--require-ok",
        action="store_true",
        help="refuse the checkpoint when the verify result is not ok",
    )
    args = ap.parse_args()

    proj = Path(args.project_dir).resolve()
    now = dt.datetime.now().astimezone()
    cp_id = f"cp-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}"

    verify = None
    verify_run_path = None
    if args.verify_json:
        verify_run_path = Path(args.verify_json)
        verify = _read_json(verify_run_path)

    if args.require_ok:
        if verify is None:
            runs_dir = proj / "verify_runs"
            try:
                runs = [p for p in runs_dir.glob("*.json") if p.is_file()]
            except OSError:
                runs = []
            if runs:
                verify_run_path = max(runs, key=lambda p: p.stat().st_mtime)
                verify = _read_json(verify_run_path)
        if verify is None:
            print("ERROR: --require-ok: no verify run found — run factory_verify.py first", file=sys.stderr)
            return 2
        if not verify.get("ok"):
            print("ERROR: verify failed — refusing checkpoint (use --status blocked)", file=sys.stderr)
            return 1

    commit = None
    backup = None
    diff_stat = None
    dirty = []

    if _is_repo(proj):
        _git(["add", "-A"], proj)
        msg = f"factory checkpoint {cp_id}" + (f": {args.task}" if args.task else "")
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", msg],
            cwd=proj, capture_output=True, text=True,
        )
        commit = _git(["rev-parse", "--short", "HEAD"], proj).strip() or None
        stat = _git(["diff", "--stat", "HEAD~1", "HEAD"], proj).strip()
        diff_stat = stat or None
        dirty = [
            line for line in _git(["status", "--porcelain"], proj).splitlines()
            if line.strip()
        ]
    else:
        backups = proj / "backups"
        backups.mkdir(parents=True, exist_ok=True)
        tar_path = backups / f"project-{cp_id}.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tf:
            for p in sorted(proj.iterdir()):
                if p.name in {".git", "backups", "__pycache__"}:
                    continue
                if p.is_file():
                    tf.add(p, arcname=p.name)
                elif p.is_dir():
                    tf.add(p, arcname=p.name)
        backup = str(tar_path)

    verify_text = "not run"
    if verify:
        checks = verify.get("checks", [])
        passed = sum(1 for c in checks if c.get("passed"))
        verify_text = f"ok={verify.get('ok')} ({passed}/{len(checks)} checks passed)"

    handoff = proj / "HANDOFF.md"
    lines = [
        f"\n## [{now.strftime('%Y-%m-%d %H:%M')}] — {cp_id}",
        f"- Task: {args.task or '(unspecified)'}",
        f"- Status: {args.status}",
        f"- Verify: {verify_text}",
    ]
    if args.notes:
        lines.append(f"- Notes: {args.notes}")
    entry = "\n".join(lines) + "\n"
    existing = handoff.read_text() if handoff.exists() else "# HANDOFF\n"
    handoff.write_text(existing.rstrip() + "\n\n" + entry)

    cp = {
        "id": cp_id,
        "time": now.isoformat(timespec="seconds"),
        "task": args.task,
        "status": args.status,
        "commit": commit,
        "backup": backup,
        "diff_stat": diff_stat,
        "dirty_files": dirty,
        "verify": verify,
    }
    if verify_run_path is not None:
        cp["verify_run"] = str(verify_run_path)
    (proj / "checkpoint.json").write_text(json.dumps(cp, indent=2) + "\n")

    print(cp_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
