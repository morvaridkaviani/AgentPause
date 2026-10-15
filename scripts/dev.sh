#!/usr/bin/env bash
# Start the API (:8000) and the web app (:3100) together for local development.
# Ctrl+C stops both. Requires `make install` (or the steps in docs/getting_started.md) first.
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PY:-.venv/bin/python}"
API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3100}"

"$PY" -m uvicorn app.main:app --app-dir backend --reload --port "$API_PORT" &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT INT TERM

BACKEND_URL="http://localhost:$API_PORT" npm run dev --workspace frontend -- --port "$WEB_PORT"
