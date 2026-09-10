#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "=========================================================="
echo "  ⚖️  Digital Legal Aid System (DLAS) — Demo Launcher"
echo "=========================================================="

# 1. Check Python virtual environment
if [ ! -d "backend/.venv" ]; then
    echo "Creating Python virtual environment in backend/.venv..."
    python3 -m venv backend/.venv
    ./backend/.venv/bin/pip install --upgrade pip
    ./backend/.venv/bin/pip install -r backend/requirements.txt
fi

# 2. Cleanup handler for graceful shutdown
cleanup() {
    echo ""
    echo "Shutting down DLAS backend and frontend..."
    kill "$BACKEND_PID" 2>/dev/null || true
    kill "$FRONTEND_PID" 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 3. Start Backend
echo "Starting Backend on http://127.0.0.1:8000 ..."
./backend/run.sh &
BACKEND_PID=$!

# 4. Start Frontend
echo "Starting Frontend on http://127.0.0.1:3000 ..."
python3 -m http.server 3000 --directory src &
FRONTEND_PID=$!

sleep 1

echo ""
echo "=========================================================="
echo "  🚀 DLAS is running!"
echo "  - Frontend Portal:    http://localhost:3000"
echo "  - Backend API & Docs: http://localhost:8000/docs"
echo "  - Health Endpoint:    http://localhost:8000/api/v1/health"
echo "  - WebSocket Server:   ws://localhost:8000/ws"
echo ""
echo "  Demo Credentials:"
echo "    DLAO Officer: officer@dlas.gov.bd / officer123"
echo "    Panel Lawyer: lawyer@dlas.gov.bd / lawyer123"
echo "    Admin:        admin@dlas.gov.bd / admin123"
echo ""
echo "  Press Ctrl+C to stop all servers."
echo "=========================================================="

wait
