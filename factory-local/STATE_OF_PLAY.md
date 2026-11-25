# Factory state of play — 2026-11-23

## State of play

- **Factory: functional (offline, local Builder `ollama/qwen3:4b-32k` —
  32k context)** — the verified model; the factory works offline with it.
- **Shootum milestone — verified — removed.** The Shootum milestone (the
  Shootum game, title "Shootum") was verified: the Shootum game runs as it
  should (user confirmed). It was the factory test.
- **Test projects — removed.** `shootum-model-a` (`ollama/qwen3:4b`),
  `shootum-model-b` (`ollama/kirito1/qwen3-coder:latest`), and `test1` — the
  Shootum milestone + test projects — removed.
- **Documents** now: the factory set (`factory-local`, `usage-meters`, ...) —
  the factory is ready for a new software project.

## Steps forward

1. **New software project:** set up a new factory project — `mkdir` a new
   project folder, `git init`, set the git identity, add the factory tasks
   with `python3 /home/username/Documents/factory-local/tools/factory_task.py
   --project-dir <new project> add "<task>"`, set the project's `opencode.json`
   model to `ollama/qwen3:4b-32k`.
2. **Continue offline.** Builder `ollama/qwen3:4b-32k` (the verified local
   model, now with 32k context).
3. **New models:** keep pulling and probing (write-tool checks) — tell me what
   you find.

## Course correction if required

- **Local-model write tool issues:** some models emit the `write` call as
  text (the tool doesn't execute — the round fails, no file). Verified
  reliable Builder: `ollama/qwen3:4b-32k`. The new model
  `ollama/kirito1/qwen3-coder:latest` — the write executes (verified). If a
  model's writes are unreliable, the fallback: drive the rounds (write the
  file via the write tool, then run the factory tools per round) — the factory
  artifacts (HANDOFF, checkpoint, tasks, verify runs) stay the source of
  truth.
- The Shootum milestone passed (the game runs as it should) — the factory is
  functional — the factory is ready for a new software project.
