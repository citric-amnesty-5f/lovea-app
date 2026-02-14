#!/bin/bash

# Quick Mobile Access Info Script
# Shows all the URLs you need to access LoveAI on mobile

echo ""
echo "📱 LoveAI Mobile Access Information"
echo "===================================="
echo ""

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['tunnels'][0]['public_url'] if data.get('tunnels') else 'NOT RUNNING')" 2>/dev/null)

# Get local IP
LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')

echo "🌐 Backend (ngrok):"
echo "   $NGROK_URL"
echo ""

echo "💻 Frontend (local network):"
echo "   http://localhost:3000 (on this computer)"
echo "   http://$LOCAL_IP:3000 (on same WiFi)"
echo ""

echo "🧪 Test Page:"
echo "   http://localhost:3000/test-ngrok.html"
echo "   http://$LOCAL_IP:3000/test-ngrok.html"
echo ""

echo "📊 ngrok Dashboard:"
echo "   http://localhost:4040"
echo ""

# Check services status
echo "📡 Service Status:"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Backend running (port 8000)"
else
    echo "   ❌ Backend NOT running"
fi

if nc -z localhost 3000 2>/dev/null; then
    echo "   ✅ Frontend running (port 3000)"
else
    echo "   ❌ Frontend NOT running"
fi

if [ "$NGROK_URL" != "NOT RUNNING" ]; then
    echo "   ✅ ngrok tunnel active"
else
    echo "   ❌ ngrok NOT running - start with: ngrok http 8000"
fi

echo ""
echo "📖 For detailed instructions, see: SETUP-COMPLETE.md"
echo ""
