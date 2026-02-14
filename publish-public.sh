#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
DIST_DIR="$ROOT_DIR/dist"
NGROK_BIN="${NGROK_BIN:-ngrok}"
APP_DOMAIN="${APP_DOMAIN:-}"

echo "==> Building frontend bundle (dist/)"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
cp "$ROOT_DIR/index.html" "$ROOT_DIR/styles.css" "$ROOT_DIR/config.js" "$DIST_DIR/"
cp -R "$ROOT_DIR/js" "$DIST_DIR/js"

echo "==> Restarting backend on :8000 (SERVE_FRONTEND=true)"
if lsof -tiTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
  EXISTING_BACKEND_PIDS="$(lsof -tiTCP:8000 -sTCP:LISTEN | tr '\n' ' ')"
  echo "Stopping existing process(es): $EXISTING_BACKEND_PIDS"
  kill $EXISTING_BACKEND_PIDS || true
  sleep 1
fi

cd "$BACKEND_DIR"
SERVE_FRONTEND=true "$BACKEND_DIR/venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 >/tmp/loveai-public-backend.log 2>&1 &
BACKEND_PID=$!
cd "$ROOT_DIR"

for _ in $(seq 1 20); do
  if curl -sS --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -sS --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
  echo "Backend failed to start. Last logs:"
  tail -n 80 /tmp/loveai-public-backend.log || true
  exit 1
fi

echo "==> Restarting ngrok"
if lsof -tiTCP:4040 -sTCP:LISTEN >/dev/null 2>&1; then
  EXISTING_NGROK_PID="$(lsof -tiTCP:4040 -sTCP:LISTEN | head -n 1)"
  echo "Stopping existing ngrok process: $EXISTING_NGROK_PID"
  kill "$EXISTING_NGROK_PID" || true
  sleep 1
fi

if [ -n "$APP_DOMAIN" ]; then
  echo "Starting ngrok with custom domain: $APP_DOMAIN"
  "$NGROK_BIN" http --url "https://$APP_DOMAIN" 8000 >/tmp/loveai-public-ngrok.log 2>&1 &
else
  echo "Starting ngrok with assigned public URL"
  "$NGROK_BIN" http 8000 >/tmp/loveai-public-ngrok.log 2>&1 &
fi
NGROK_PID=$!
sleep 3

if ! kill -0 "$NGROK_PID" >/dev/null 2>&1; then
  echo "ngrok failed to start:"
  cat /tmp/loveai-public-ngrok.log || true
  if rg -q "ERR_NGROK_314" /tmp/loveai-public-ngrok.log 2>/dev/null; then
    echo ""
    echo "Custom domain endpoints require a paid ngrok plan."
    echo "Run again without APP_DOMAIN to publish on a free ngrok URL:"
    echo "  ./publish-public.sh"
  fi
  exit 1
fi

PUBLIC_URL="$(curl -sS http://127.0.0.1:4040/api/tunnels | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["tunnels"][0]["public_url"] if d.get("tunnels") else "")' 2>/dev/null || true)"

if [ -z "$PUBLIC_URL" ]; then
  PUBLIC_URL="$(rg -o 'url=https://[^ ]+' /tmp/loveai-public-ngrok.log | head -n1 | cut -d= -f2 || true)"
fi

echo ""
echo "✅ LoveAI is published from this computer"
echo "Backend PID: $BACKEND_PID"
echo "ngrok PID:   $NGROK_PID"
echo "Public URL:  ${PUBLIC_URL:-<check /tmp/loveai-public-ngrok.log>}"
echo ""
echo "Open this URL in any browser/device:"
echo "  ${PUBLIC_URL:-<not-detected>}"
echo ""
echo "Logs:"
echo "  tail -f /tmp/loveai-public-backend.log"
echo "  tail -f /tmp/loveai-public-ngrok.log"
echo ""
echo "To stop:"
echo "  kill $BACKEND_PID $NGROK_PID"
