# Factory Tutorial — running Factory Lite with local and online models

Two factories are set up here:

- **`factory-lite`** (online) — `/home/username/Documents/factory-lite/` — projects default to the zero-cost catalog Builder (`opencode/tidepool-alpha-free`).
- **`factory-local`** (offline) — `/home/username/Documents/factory-local/` — projects default to the local Builder `ollama/qwen3.5:9b-32k`.

Start a project: `bash /home/username/Documents/<factory>/start_new_project.sh <name>` or double-click `Factory_Lite — New Project` / `Factory_Local — New Project` on the Desktop. Then run the Builder: `opencode run --auto "Play the Factory Builder role per /home/username/Documents/<factory>/roles/builder.md — start with factory_task #1"` in the new project.

## Key config that made local models work through opencode

`~/.config/opencode/opencode.json` (global) and each project's `opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "providers": {
    "ollama": {
      "options": {
        "headerTimeout": 1200000,
        "chunkTimeout": 0,
        "timeout": 1200000
      }
    }
  }
}
```

`chunkTimeout: 0` is the important one for local models — the direction of the upstream PR "Increase chunk timeout & auto-disable for local URLs" (opencode#2974, fixed in #3229). It stops "Timed out waiting for response headers" for slow local models.

## Local models: status

- `ollama/qwen3.5:9b-32k` — completes Builder rounds (verified).
- `opencode/tidepool-alpha-free` (zero-cost catalog) — completes rounds reliably (the default).
- `ollama/kirito1/qwen3-coder-32k`, `ollama/qwen3:4b-32k`, `ollama/qwen3:8b-32k`, `ollama/qwen2.5-coder:7b-32k` — still have opencode-side issues (tool-call format / fetch timeouts).

## Local model context sizes

Models run with 32k context via per-model variants (`ollama create` with `FROM <base>` + `PARAMETER num_ctx 32768`; Modelfiles in `/home/username/Documents/ollama-32k/`). The server-level default is `OLLAMA_CONTEXT_LENGTH` (default 4096) — raised by editing `/etc/systemd/system/ollama.service` and restarting the service (root required).

## Useful GitHub issues

- Header timeouts with slow local providers: `anomalyco/opencode#26602`, `#56371`, `#55447`, `#29548`.
- Tool-calling gaps with local models: `anomalyco/opencode#4428` ("classic tool calling capability gap"), `#234`, `#46625`, `#20836`, `#33959`.
- Local model + Ollama context: ollama.com/docs/context-length.

## Notes for a repo you publish

- Start with the online factory (`factory-lite`): its zero-cost catalog Builder reliably completes rounds — no local setup needed.
- For offline: default the Builder to `ollama/qwen3.5:9b-32k` (as in `factory-local/start_new_project.sh`), and set `providers.ollama.options` as above in global + project configs.
