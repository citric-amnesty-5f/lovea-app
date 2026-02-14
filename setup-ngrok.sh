#!/bin/bash

# Simple ngrok setup script for LoveAI
# This script helps you configure and start ngrok tunnels

echo "🔗 LoveAI ngrok Setup"
echo "===================="
echo ""

# Check if servers are running
if ! nc -z localhost 8000 2>/dev/null; then
    echo "⚠️  Backend is not running on port 8000"
    echo "   Start it with: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo ""
fi

if ! nc -z localhost 3000 2>/dev/null; then
    echo "⚠️  Frontend is not running on port 3000"
    echo "   Start it with: python3 -m http.server 3000"
    echo ""
fi

# Check ngrok authentication
echo "📋 Checking ngrok setup..."
if ! ngrok config check &>/dev/null; then
    echo ""
    echo "🔑 ngrok needs authentication:"
    echo "   1. Visit: https://dashboard.ngrok.com/signup"
    echo "   2. Sign up for free account"
    echo "   3. Copy your authtoken"
    echo "   4. Run: ngrok authtoken YOUR_TOKEN_HERE"
    echo ""
    read -p "Have you set up your ngrok authtoken? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please set up ngrok authtoken first!"
        exit 1
    fi
fi

echo ""
echo "🚀 Starting ngrok tunnels..."
echo ""

# Start ngrok for backend
echo "Starting backend tunnel (port 8000)..."
ngrok http 8000 > /dev/null &
NGROK_PID=$!
sleep 3

# Get the public URL
BACKEND_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else '')" 2>/dev/null)

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Failed to get ngrok URL"
    echo "   Visit http://localhost:4040 to see your tunnel URL"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Backend tunnel is ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Your backend URL: $BACKEND_URL"
echo ""
echo "🔧 Next steps:"
echo ""
echo "1. Update js/backend-api.js:"
echo "   Change: const API_BASE_URL = 'http://localhost:8000';"
echo "   To:     const API_BASE_URL = '$BACKEND_URL';"
echo ""
echo "2. Open frontend in browser:"
echo "   http://localhost:3000"
echo ""
echo "3. Or access from your phone on same WiFi:"
echo "   Find your IP: ifconfig | grep 'inet '"
echo "   Then visit: http://YOUR_IP:3000"
echo ""
echo "📊 View ngrok dashboard: http://localhost:4040"
echo ""
echo "Press Ctrl+C to stop ngrok..."

# Keep running
wait $NGROK_PID
