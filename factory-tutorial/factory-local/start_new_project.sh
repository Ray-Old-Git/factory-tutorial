#!/usr/bin/env bash
# Factory Lite — start a new software project.
# Usage: ./start_new_project.sh <project-name>
# Creates ~/Documents/<name>, initializes git, sets the git identity,
# configures the factory (Builder model + MCP server), and adds the factory tasks.
set -eu

name="${1:?Usage: start_new_project.sh <project-name>}"
proj="/home/ray/Documents/$name"

mkdir -p "$proj"
cd "$proj"

if [ ! -d .git ]; then
  git init -q
fi
git config user.name "Ray"
git config user.email "ray@localhost"

if [ ! -f README.md ]; then
  printf '# %s\n' "$name" > README.md
fi

printf '{\n  "$schema": "https://opencode.ai/config.json",\n  "model": "ollama/qwen3.5:9b-32k",\n  "mcp": {"servers": {"factory": {"type": "local", "command": ["python3", "/home/ray/Documents/factory-local/tools/factory_mcp.py"]}}}\n}\n' > opencode.json

FT=/home/ray/Documents/factory-local/tools/factory_task.py
python3 $FT --project-dir "$proj" add "Create game.py: game controller with the game loop, 10 shots per turn (window title 'Shootum'), quit after the shots run out, and placeholder drawing. Import only pygame so it runs standalone."
python3 $FT --project-dir "$proj" add "Implement player.py: player movement (keyboard) + shooting (space = fire bullet)."
python3 $FT --project-dir "$proj" add "Implement targets.py: target generator + target types (red/blue/green) with positions and speeds."
python3 $FT --project-dir "$proj" add "Implement ui.py: game UI + scoreboard display."
python3 $FT --project-dir "$proj" add "Implement audio.py: audio feedback for shooting and hits."
python3 $FT --project-dir "$proj" add "Complete game.py: integrate player/targets/ui/audio, add the game-over screen, and finalize acceptance criteria (movement, targets spawn, game over at 0 shots, +10 per hit)."

echo "Created project: $proj"
echo "Run the factory: opencode run --auto \"Play the Factory Builder role per /home/ray/Documents/factory-local/roles/builder.md — start with factory_task #1\""
