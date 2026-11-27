# Factory Lite v2

A tool-enforced, resumable software factory setup for a small game project,
sized for a low-VRAM local machine.

## Components

- `tools/factory_verify.py` — deterministic checks (syntax, smoke run, unit
  tests); prints JSON. Each run is saved to `verify_runs/` automatically.
- `tools/factory_checkpoint.py` — snapshot: git commit (or tarball backup) +
  appends to `HANDOFF.md` + writes `checkpoint.json`. With `--require-ok` it
  refuses to checkpoint when the newest verify run (or `--verify-json`) is
  not ok.
- `tools/factory_resume.py` — startup inspection (handoff, git log/status,
  verify state, open tasks) with consistency warnings.
- `tools/factory_review_packet.py` — builds a redacted diff + summary packet
  for the online reviewer.
- `tools/factory_task.py` — tiny task manager (`list`/`add`/`start`/`done`/
  `next`, state in `tasks.json`).
- `roles/` — `planner.md`, `builder.md`, `auditor.md`, `human_tester.md` role
  prompts.
- `FACTORY_PROPOSAL.md` — the design notes and the reliability/productivity
  brainstorms.

## Recommended models (this machine: GTX 1050 Ti 4 GB VRAM, 15 GB RAM, 4 cores)

- **Builder (coding):** local `ollama/qwen3:4b-32k` (built from the verified
  `ollama/qwen3:4b`, now with 32k context; ~6.4 GB loaded on this box) — it
  calls tools through OpenCode — verified: the shell and write tools execute.
  Set as the project default via `opencode.json` — the factory's Builder now
  (new projects default to it via `start_new_project.sh`). The zero-cost
  catalog model `opencode/tidepool-alpha-free` is the alternative.
- **Priority:** the factory working reliably OFFLINE with local models — the
  Builder is the verified local model (`ollama/qwen3:4b`).
- **Auditor (review):** `qwen3.5:9b` (6.2 GB — fits the 15 GB RAM, slow on 4
  cores) or another zero-cost catalog entry via `/models`.

## Flow

Planner (adds one task per feature with `factory_task add`) → Builder rounds
(`factory_task next`/`start` → edit → `factory_verify` → `factory_task done` → `factory_checkpoint --require-ok`) → Auditor (`factory_review_packet`,
approval-gated) → Human Tester (build + report, approval-gated).

Builder rule of thumb on this box: at most two fix attempts per feature; if it
still fails, checkpoint `--status blocked` and switch to a bigger local model
or ask for human review.

## First run

1. New folder: `cd` to your game project; `git init` if you have git (it is
   not installed on this machine — `sudo apt install git` if you want the git
   path; otherwise the tools save tarball backups in `backups/`).
2. Assign the Builder model via `/models` in OpenCode.
3. Paste `roles/planner.md` and ask OpenCode to play the Planner.
