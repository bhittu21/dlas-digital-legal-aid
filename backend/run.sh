#!/usr/bin/env bash
set -e

# Change directory to backend directory
cd "$(dirname "$0")"

# Detect virtual environment
if [ -f ".venv/bin/uvicorn" ]; then
    UVICORN_BIN=".venv/bin/uvicorn"
else
    UVICORN_BIN="uvicorn"
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo "=========================================================="
echo "  Starting Digital Legal Aid System (DLAS) Backend"
echo "  Binding to: http://${HOST}:${PORT}"
echo "  Docs:       http://${HOST}:${PORT}/docs"
echo "  Health:     http://${HOST}:${PORT}/api/v1/health"
echo "  WebSocket:  ws://${HOST}:${PORT}/ws"
echo "=========================================================="

exec "$UVICORN_BIN" app.main:app --host "$HOST" --port "$PORT" --reload
