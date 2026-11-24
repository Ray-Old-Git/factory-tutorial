#!/usr/bin/env python3
"""factory_task — tiny task manager for the Factory Lite pipeline.

Usage:
    python3 tools/factory_task.py --project-dir DIR <command> [args]

Commands:
    list [--status STATUS]  — print tasks (STATUS: pending|in_progress|done|all)
    add "text"              — add a pending task; prints the new task id
    start ID                — mark ID in_progress
    done ID                 — mark ID done (records done_at)
    next                    — print the next pending task

State: <project>/tasks.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path


def _load(proj: Path):
    try:
        return json.loads((proj / "tasks.json").read_text())
    except Exception:
        return {"next_id": 1, "tasks": []}


def _save(proj: Path, state):
    (proj / "tasks.json").write_text(json.dumps(state, indent=2) + "\n")


def _find(state, task_id):
    for t in state.get("tasks", []):
        if t.get("id") == task_id:
            return t
    return None


def _now():
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def main() -> int:
    ap = argparse.ArgumentParser(description="Factory task manager.")
    ap.add_argument("--project-dir", default=".", help="project folder (default: cwd)")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("list", help="print tasks")
    p.add_argument("--status", default="all", help="pending|in_progress|done|all")

    p = sub.add_parser("add", help="add a pending task")
    p.add_argument("text")

    p = sub.add_parser("start", help="mark a task in_progress")
    p.add_argument("id", type=int)

    p = sub.add_parser("done", help="mark a task done")
    p.add_argument("id", type=int)

    p = sub.add_parser("next", help="print the next pending task")

    args = ap.parse_args()
    proj = Path(args.project_dir).resolve()
    state = _load(proj)

    if args.command == "list":
        for t in state.get("tasks", []):
            if args.status != "all" and t.get("status") != args.status:
                continue
            done_note = f" (done {t['done_at']})" if t.get("done_at") else ""
            print(f"- #{t.get('id')} [{t.get('status')}] {t.get('text')}{done_note}")
        if not state.get("tasks"):
            print("(no tasks)")
        return 0

    if args.command == "add":
        task_id = state.get("next_id", 1)
        state["next_id"] = task_id + 1
        state.setdefault("tasks", []).append({
            "id": task_id,
            "status": "pending",
            "text": args.text,
            "created": _now(),
        })
        _save(proj, state)
        print(task_id)
        return 0

    if args.command in ("start", "done"):
        task = _find(state, args.id)
        if not task:
            print(f"ERROR: no task #{args.id}", file=sys.stderr)
            return 1
        task["status"] = "in_progress" if args.command == "start" else "done"
        if args.command == "done":
            task["done_at"] = _now()
        _save(proj, state)
        print(f"#{args.id}: {task['status']}")
        return 0

    if args.command == "next":
        for t in state.get("tasks", []):
            if t.get("status") == "pending":
                print(f"#{t.get('id')} {t.get('text')}")
                return 0
        print("(no pending tasks)")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
