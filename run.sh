#!/usr/bin/env bash
# Launch both the FastAPI bridge (voice page + scorer endpoints) and the
# Streamlit hub (scenarios + history).
#
# Bridge:   http://localhost:8000
# Streamlit: http://localhost:8511
set -euo pipefail

cd "$(dirname "$0")"

if [ ! -f .env ]; then
  echo "⚠️  No .env file found. Copy .env.example to .env and fill in:"
  echo "    ANTHROPIC_API_KEY   (required for scoring)"
  echo "    OPENAI_API_KEY      (required for voice sessions)"
  echo
fi

# Free up ports if a previous run left things hanging
pkill -f "uvicorn server:app" 2>/dev/null || true
pkill -f "streamlit run streamlit_app.py" 2>/dev/null || true
sleep 1

# Background: FastAPI bridge
mkdir -p /tmp/komodo-trainer
nohup python3 -m uvicorn server:app --host 127.0.0.1 --port 8000 \
  > /tmp/komodo-trainer/bridge.log 2>&1 &
BRIDGE_PID=$!
echo "Bridge started (PID $BRIDGE_PID) — log: /tmp/komodo-trainer/bridge.log"

# Wait briefly for it to come up
for i in 1 2 3 4 5; do
  if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
    break
  fi
  sleep 0.6
done

if curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1; then
  echo "✅ Bridge ready at http://localhost:8000"
else
  echo "⚠️  Bridge didn't come up cleanly — check /tmp/komodo-trainer/bridge.log"
fi

# Trap to clean up the bridge when streamlit exits
trap "echo; echo Stopping bridge…; kill $BRIDGE_PID 2>/dev/null || true" EXIT INT TERM

# Foreground: Streamlit (so Ctrl+C kills both)
echo
echo "Starting Streamlit on http://localhost:8511 …"
python3 -m streamlit run streamlit_app.py --server.port 8511
