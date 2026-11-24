#!/usr/bin/env python3
"""factory_verify — deterministic checks for the Factory Lite pipeline.

Usage:
    python3 tools/factory_verify.py [--project-dir DIR] [--main FILE] [--timeout SEC]

Checks (in order):
  1. syntax — `python3 -m py_compile <main>`
  2. smoke  — run `python3 <main>` with a timeout; passed when the process is
     still running when the timeout fires, or exits 0, and no "Traceback"
     appears in the output.
  3. unit tests — `python3 -m unittest discover`; skipped when the project has
     no test files.

Output: one JSON object on stdout:
    {"ok": bool, "checks": [{"name", "passed", "detail"}], "log": str}
Exit code: 0 when ok, 1 otherwise.
Each run is also saved to `<project>/verify_runs/verify-<stamp>.json` when the
directory can be written.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import secrets
import subprocess
import sys
from pathlib import Path

TRACEBACK_MARKER = "Traceback (most recent call last)"


def _run(cmd, cwd=None, timeout=None):
    """Return (returncode, output, timed_out); timed_out means the command was
    killed by the timeout (returncode is None then)."""
    try:
        p = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, (p.stdout or "") + "\n" + (p.stderr or ""), False
    except subprocess.TimeoutExpired as e:
        out = e.stdout or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", "replace")
        err = e.stderr or ""
        if isinstance(err, bytes):
            err = err.decode("utf-8", "replace")
        return None, (out or "") + "\n" + (err or ""), True


def main() -> int:
    ap = argparse.ArgumentParser(description="Run Factory Lite deterministic checks.")
    ap.add_argument("--project-dir", default=".", help="project folder (default: cwd)")
    ap.add_argument("--main", default="game.py", help="main file (default: game.py)")
    ap.add_argument("--timeout", type=float, default=15.0, help="seconds for the smoke run")
    args = ap.parse_args()

    proj = Path(args.project_dir).resolve()
    main_file = proj / args.main
    checks = []
    log_parts = []

    # 1. syntax
    rc, out, _ = _run([sys.executable, "-m", "py_compile", str(main_file)], cwd=proj)
    checks.append({
        "name": "syntax",
        "passed": rc == 0,
        "detail": f"py_compile exit={rc}",
    })
    log_parts.append("--- syntax ---\n" + out)

    # 2. smoke
    rc, out, timed_out = _run(
        [sys.executable, str(main_file)], cwd=proj, timeout=args.timeout
    )
    if timed_out:
        smoke_ok = TRACEBACK_MARKER not in out
        detail = f"no crash in first {args.timeout:g}s (process still running when stopped)"
    else:
        smoke_ok = rc == 0 and TRACEBACK_MARKER not in out
        detail = f"exit={rc}"
    checks.append({"name": "smoke", "passed": smoke_ok, "detail": detail})
    log_parts.append("--- smoke ---\n" + out)

    # 3. unit tests (only if there are test files)
    test_files = [p for p in proj.glob("test_*.py")] + [p for p in proj.glob("*_test.py")]
    if test_files:
        rc, out, _ = _run([sys.executable, "-m", "unittest", "discover"], cwd=proj)
        checks.append({
            "name": "unit_tests",
            "passed": rc == 0,
            "detail": f"unittest discover exit={rc}",
        })
        log_parts.append("--- unit tests ---\n" + out)
    else:
        checks.append({
            "name": "unit_tests",
            "passed": True,
            "detail": "skipped: no test files",
        })

    ok = all(c["passed"] for c in checks)
    result = {"ok": ok, "checks": checks, "log": "\n".join(log_parts)[-8000:]}
    print(json.dumps(result, indent=2))

    # Save the run as evidence under verify_runs/
    stamp = dt.datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    try:
        run_dir = proj / "verify_runs"
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / f"verify-{stamp}-{secrets.token_hex(2)}.json").write_text(
            json.dumps(result, indent=2) + "\n"
        )
    except OSError:
        pass

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
