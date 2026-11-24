#!/usr/bin/env bash
# Factory Lite — start the project: print the resume sheet and open the
# project folder, so you can continue after startup.
set -u

FACTORY=/home/ray/Documents/factory-local
cd "$FACTORY"

echo "== Factory Lite: resume sheet =="
python3 tools/factory_resume.py --project-dir "$FACTORY" || true

echo
echo "== Opening the project folder =="
# The game project folder (set the path as an argument when the game project
# exists). Falls back to the factory folder until it does.
PROJ="${1:-/home/ray/Documents/game-project}"
[ -d "$PROJ" ] || PROJ="$FACTORY"
xdg-open "$PROJ" >/dev/null 2>&1 || true
echo "project: $PROJ"
