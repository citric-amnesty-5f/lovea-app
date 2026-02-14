#!/bin/bash

# LoveAI Mobile Deployment Script using ngrok
# This script starts backend, frontend, and exposes them via ngrok

set -e

echo "🚀 Starting LoveAI for Mobile Access..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $(jobs -p) 2>/dev/null || true
    exit
}
trap cleanup EXIT INT TERM

# Step 1: Start Backend
echo -e "${BLUE}📡 Starting Backend Server (Port 8000)...${NC}"
cd "$SCRIPT_DIR/backend"
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/loveai-backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✓ Backend started (PID: $BACKEND_PID)${NC}"
sleep 3

# Step 2: Start Frontend
echo -e "${BLUE}🌐 Starting Frontend Server (Port 3000)...${NC}"
cd "$SCRIPT_DIR"
if command -v python3 &> /dev/null; then
    python3 -m http.server 3000 > /tmp/loveai-frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo -e "${GREEN}✓ Frontend started (PID: $FRONTEND_PID)${NC}"
else
    echo -e "${YELLOW}⚠ Python3 not found, please start frontend manually${NC}"
fi
sleep 2

# Step 3: Start ngrok for Backend
echo ""
echo -e "${BLUE}🔗 Creating public URL for Backend...${NC}"
ngrok http 8000 --log=stdout > /tmp/loveai-ngrok-backend.log 2>&1 &
NGROK_BACKEND_PID=$!
sleep 4

# Extract backend ngrok URL
BACKEND_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$BACKEND_URL" ]; then
    echo -e "${YELLOW}⚠ Could not get ngrok URL automatically${NC}"
    echo "Please visit http://localhost:4040 to see your ngrok URLs"
    BACKEND_URL="CHECK_NGROK_DASHBOARD"
else
    echo -e "${GREEN}✓ Backend URL: $BACKEND_URL${NC}"
fi

# Step 4: Start ngrok for Frontend (on different port)
echo -e "${BLUE}🔗 Creating public URL for Frontend...${NC}"
ngrok http 3000 --log=stdout > /tmp/loveai-ngrok-frontend.log 2>&1 &
NGROK_FRONTEND_PID=$!
sleep 4

# Extract frontend ngrok URL
FRONTEND_URL=$(curl -s http://localhost:4041/api/tunnels 2>/dev/null | grep -o '"public_url":"https://[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$FRONTEND_URL" ]; then
    # Try alternate ngrok API port
    echo -e "${YELLOW}⚠ Starting second ngrok instance...${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✅ LoveAI is now accessible on mobile!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}📱 Access from your phone:${NC}"
echo ""
echo -e "   Backend:  ${YELLOW}$BACKEND_URL${NC}"
echo -e "   Frontend: Check ngrok dashboard below"
echo ""
echo -e "${BLUE}🖥  Local URLs (same WiFi only):${NC}"
echo ""
echo -e "   Backend:  ${YELLOW}http://localhost:8000${NC}"
echo -e "   Frontend: ${YELLOW}http://localhost:3000${NC}"
echo ""
echo -e "${BLUE}📊 ngrok Dashboard:${NC}"
echo ""
echo -e "   ${YELLOW}http://localhost:4040${NC} (Backend tunnels)"
echo ""
echo -e "${YELLOW}⚠ IMPORTANT: Update js/backend-api.js with your backend URL!${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f /tmp/loveai-backend.log"
echo "   Frontend: tail -f /tmp/loveai-frontend.log"
echo ""
echo "Press Ctrl+C to stop all services..."
echo ""

# Keep script running
wait
