# Factory Lite v2 — design & brainstorms

## Summary

A tool-enforced, resumable factory for the game project, sized for a
low-VRAM local machine:

- `tools/factory_verify.py` — deterministic checks → JSON
- `tools/factory_checkpoint.py` — snapshot + HANDOFF.md + checkpoint.json
- `tools/factory_resume.py` — startup inspection
- `tools/factory_review_packet.py` — redacted diff + summary for online review
- `roles/` — Planner / Builder / Auditor / Human-Tester prompts

See `README.md` for the model split for this machine.

## Implemented in v2

- Tool-enforced gates — `factory_checkpoint --require-ok` (refuses with exit 1
  when the verify result is not ok; exit 2 when there is no verify run).
- Automatic evidence — every `factory_verify` run is saved under
  `verify_runs/`; `checkpoint.json` records the `verify_run` it embeds.
- Consistency & task management — `tools/factory_task.py` (add/start/done/
  next/list, state in `tasks.json`); `factory_resume.py` prints open tasks;
  the artifact system (HANDOFF, checkpoint, verify_runs, backups) carries
  state across sessions.

## Brainstorm: reliability improvements

1. **Deterministic tools as the core** — all state transitions go through
   factory_verify / factory_checkpoint / factory_resume; agents act on the
   JSON output, never on prose.
2. **Structured outputs everywhere** — verify JSON (checks + log tail),
   checkpoint.json (id/time/commit/verify/dirty), HANDOFF.md
   (append-only). A resume reads them all as data.
3. **Tool-enforced gates** — `--require-ok` (implemented), `--verify-json`
   embeds the verify in the checkpoint.
4. **Resume cross-checks** — warnings when HANDOFF says "done" but the
   last verify didn't pass, or when nothing changed since the last
   checkpoint.
5. **Failure caps and escalation** — Builder: max two fix attempts per
   feature; after N stalled attempts: switch to a bigger local model or stop
   and ask the user. Time budget per round.
6. **Evidence preservation** — on stall: checkpoint (status "blocked") +
   verify runs are auto-saved under `verify_runs/` (implemented).
7. **Atomic handoffs** — HANDOFF is append-only; checkpoints always get a
   commit (or backup); tools never delete or overwrite.
8. **Small-model friendliness** — literal rules ("run verify, if ok:
   checkpoint with --status done"), checklists over prose; tools print short
   summaries.
9. **Serialize agents** — the 4-core box: run Builder, then Auditor. Resume
   prints the next step. Later, if hardware allows, overlap milestone review
   with the next build.

## Brainstorm: productivity improvements

1. **Model specialization** — Builder on `ollama/qwen3:4b` (local, 2.5 GB —
   calls tools through OpenCode — verified: the shell and write tools execute;
   the zero-cost catalog model `opencode/tidepool-alpha-free` is the
   alternative); Auditor on `qwen3.5:9b` (RAM-resident, good at reading diffs)
   — picked per role via OpenCode's `/models`.
2. **Role files as prompts** — planner/builder/auditor/human prompts live in
   `roles/`; sessions reference them by path.
3. **Modules per feature** — build the game in tiny modules (one module per
   feature round); each round ends with a fast verify (~seconds) so the loop
   is quick.
4. **Skip unneeded work** — unit tests skipped when no `test_*.py` exist
   (already); smoke timeout short by default (15 s).
5. **Bounded review packets** — diff since the last checkpoint commit, ≤4000
   lines, questions answerable ("does the maze gen handle walls at (x,y)?").
6. **Observability** — `factory_resume` one command = full state: handoff,
   git log, verify result.
7. **Evidence-based retries** — on the second attempt, the Builder re-runs
   verify first and pastes the new log (no blind retries).
8. **Reuse across projects** — tools are generic (`--project-dir`); keep this
   folder as a factory template.
9. **Watch the dashboard** — use the System Monitor window during rounds to
   spot VRAM pressure/swap early and downshift the model if needed.

## Factory rules

- **Open source or free only:** prefer open source or free software/engines
  for all factory work and builds — no proprietary SDKs, paid engines, or
  closed-source dependencies unless explicitly overridden by the user. The
  Shootum game uses Python + pygame (open source) for this reason.
