#!/usr/bin/env python3
"""factory_mcp — Factory Lite tools as MCP tools (stdio server).

Tools:
- checkpoint — snapshot the project (git commit or tarball backup) and
  append to HANDOFF.md + checkpoint.json.
- verify — run the deterministic checks (syntax, smoke, unit tests);
  prints JSON {ok, checks, log}.
- resume — print the factory resume sheet (HANDOFF, checkpoint, tasks, git).
- task — add/start/done/next/list tasks (state in tasks.json).

Configure in a project's opencode.json:
    {"mcp": {"servers": {"factory": {"type": "local",
        "command": ["python3", "/home/ray/Documents/factory-local/tools/factory_mcp.py"]}}}}
"""

import json
import subprocess
import sys

TOOLS_DIR = "/home/ray/Documents/factory-local/tools"
SCRIPTS = {
    "checkpoint": "factory_checkpoint.py",
    "verify": "factory_verify.py",
    "resume": "factory_resume.py",
    "task": "factory_task.py",
}


def _tool_definitions():
    return [
        {
            "name": "checkpoint",
            "description": "Snapshot the project (git commit or tarball backup) and append to HANDOFF.md + checkpoint.json.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string", "description": "Project folder"},
                    "task": {"type": "string", "description": "What was done"},
                    "status": {"type": "string", "description": "e.g. done, in-progress, blocked", "default": "checkpoint"},
                    "notes": {"type": "string", "description": "Extra notes"},
                    "verify_json": {"type": "string", "description": "Path to factory_verify JSON output"},
                    "require_ok": {"type": "boolean", "description": "Refuse the checkpoint when the verify result is not ok"},
                },
            },
        },
        {
            "name": "verify",
            "description": "Run the factory deterministic checks (syntax, smoke, unit tests); prints JSON {ok, checks, log}.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string", "description": "Project folder"},
                    "main": {"type": "string", "description": "Main file", "default": "game.py"},
                    "timeout": {"type": "number", "description": "Seconds for the smoke run"},
                },
            },
        },
        {
            "name": "resume",
            "description": "Print the factory resume sheet (HANDOFF.md, checkpoint.json, tasks, git log/status).",
            "inputSchema": {
                "type": "object",
                "properties": {"project_dir": {"type": "string", "description": "Project folder"}},
            },
        },
        {
            "name": "task",
            "description": "Task manager: commands add/start/done/next/list; state in tasks.json.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_dir": {"type": "string", "description": "Project folder"},
                    "command": {"type": "string", "description": "add/start/done/next/list"},
                    "text": {"type": "string", "description": "Task text (add)"},
                    "id": {"type": "integer", "description": "Task id (start/done)"},
                },
            },
        },
    ]


def _flatten(args):
    out = []
    for k, v in args.items():
        if v is None or v is False or v == "" or v == [] or v == {}:
            continue
        if k in ("id", "command", "text"):
            out.append(str(v))
            continue
        flag = "--" + k.replace("_", "-")
        if isinstance(v, bool):
            out.append(flag)
        else:
            out.append(flag)
            out.append(str(v))
    return out


def _run_tool(name, args):
    cmd = [sys.executable, f"{TOOLS_DIR}/{SCRIPTS[name]}"]
    # Script CLIs take "--project-dir" before any subcommand (it is a
    # main-parser arg; see factory_task.py usage line).
    proj = args.pop("project_dir", None)
    if proj:
        cmd += ["--project-dir", str(proj)]
    cmd += _flatten(args)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    out = p.stdout or ""
    if p.stderr:
        out += "\n[stderr] " + p.stderr.strip()
    return out, p.returncode


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method = req.get("method")
        req_id = req.get("id")
        if method == "initialize":
            params = req.get("params", {})
            result = {
                "protocolVersion": params.get("protocolVersion") or "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "factory-local", "version": "1.0"},
            }
        elif method == "tools/list":
            result = {"tools": _tool_definitions()}
        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            try:
                text, rc = _run_tool(name, args)
                result = {"content": [{"type": "text", "text": text}], "isError": rc != 0}
            except Exception as e:
                result = {"content": [{"type": "text", "text": f"ERROR: {e}"}], "isError": True}
        else:
            if req_id is None:
                continue
            result = {}
        if req_id is not None:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": result}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
