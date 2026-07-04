#!/bin/sh
# Start the Arisbe web UI (Organon / Ergasterion / Agon) — http://localhost:8000
# Usage: ./serve.sh [port] [extra uvicorn flags…]   e.g.  ./serve.sh 8000 --reload
cd "$(dirname "$0")" || exit 1
PORT="${1:-8000}"
[ $# -gt 0 ] && shift
exec uv run uvicorn --app-dir src web_api.main:app --port "$PORT" "$@"
