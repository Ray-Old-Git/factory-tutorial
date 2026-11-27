# Factory Lite — Read Me

The Factory Lite system: tools + roles + state for building software with a
local AI agent (OpenCode + local models). All artifacts are on disk.

## Tools (factory-local/tools/)

- `factory_verify.py` — deterministic checks: syntax, smoke run, unit tests.
  Outputs JSON. Every run is saved to `verify_runs/`.
- `factory_checkpoint.py` — snapshot (git commit or tarball backup) + append
  to `HANDOFF.md` + write `checkpoint.json`. `--require-ok` refuses the
  checkpoint when the verify result is not ok.
- `factory_resume.py` — print the resume sheet: HANDOFF.md, checkpoint.json,
  tasks, git log/status.
- `factory_review_packet.py` — build a redacted diff + summary packet for the
  online reviewer.
- `factory_task.py` — task manager: `add`/`start`/`done`/`next`/`list`, state
  in `tasks.json`.
- `factory_mcp.py` — Factory tools as MCP tools (stdio server): `checkpoint`,
  `verify`, `resume`, `task`.

## Roles (factory-local/roles/)

- `planner.md` — propose the plan (engine, features, structure, checks).
- `builder.md` — implement one feature per round: `factory_task next/start`,
  implement, `factory_verify`, `factory_task done`,
  `factory_checkpoint --require-ok`.
- `auditor.md` — review packet, approval-gated.
- `human_tester.md` — final build + report, approval-gated.

## Desktop shortcuts (Double-click on Desktop)

- **Factory Lite — Resume** — `/home/username/Desktop/Factory_Lite_Resume.desktop`
  → `factory_resume` — print the factory resume sheet (HANDOFF, checkpoint,
  tasks, git) and open the project folder. Use after a restart to see the
  current factory state and continue.
- **Factory Lite — New Project** —
  `/home/username/Desktop/Factory_New_Project.desktop` →
  `factory-local/start_new_project.sh <name>` — start a new software project:
  creates `~/Documents/<name>`, git init, identity, config (model + MCP),
  adds the factory tasks.

## Maintain the factory

- The factory state (artifacts) is on disk: `factory-local/` (tools, roles,
  state files) and the project folders.
- Start a new project: run **Factory Lite — New Project** (or
  `./start_new_project.sh <name>`).
- Start the Builder rounds: in the new project, open OpenCode, run the
  Builder role:
  ```
  opencode run --auto "Play the Factory Builder role per /home/username/Documents/factory-local/roles/builder.md — start with factory_task #1"
  ```
- After shutdown/interruption: **Factory Lite — Resume** — prints the resume
  sheet.

## The factory in one line

Planner → Builder rounds (verify → checkpoint) → Auditor (review packet,
approval) → Human Tester (build + report, approval).
