# 📱 LoveAI Mobile Setup Guide

## Quick Start with ngrok (3 Steps!)

### Step 1: Get Your ngrok Authtoken (One-time setup)

1. Visit: https://dashboard.ngrok.com/signup
2. Sign up for a free account (takes 30 seconds)
3. Copy your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken
4. Run this command:
   ```bash
   ngrok authtoken YOUR_TOKEN_HERE
   ```

### Step 2: Start Your Servers

Open 2 terminal windows:

**Terminal 1 - Backend:**
```bash
cd /Users/anilkumar/loveai-app/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd /Users/anilkumar/loveai-app
python3 -m http.server 3000
```

### Step 3: Start ngrok Tunnel

**Terminal 3 - ngrok:**
```bash
cd /Users/anilkumar/loveai-app
ngrok http 8000
```

You'll see output like:
```
Forwarding   https://abc123.ngrok.io -> http://localhost:8000
```

**Copy that URL** (e.g., `https://abc123.ngrok.io`)

### Step 4: Update Frontend Configuration

**Option A - Automatic (Recommended):**
```bash
cd /Users/anilkumar/loveai-app
node update-api-url.js https://abc123.ngrok.io
```

**Option B - Manual:**
Edit `js/backend-api.js` and change:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```
to:
```javascript
const API_BASE_URL = 'https://abc123.ngrok.io';  // Your ngrok URL
```

### Step 5: Access from Mobile

Open on your phone: `http://localhost:3000` or your computer's IP

---

## Alternative: Local Network Only (No ngrok needed)

If your phone is on the same WiFi as your computer:

1. Find your computer's IP:
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```
   You'll see something like: `inet 192.168.1.100`

2. Update `js/backend-api.js`:
   ```javascript
   const API_BASE_URL = 'http://192.168.1.100:8000';
   ```

3. Access from phone: `http://192.168.1.100:3000`

---

## Troubleshooting

### ngrok shows "tunnel not found"
- Make sure backend is running on port 8000 first
- Check: `curl http://localhost:8000/health`

### "Failed to connect" on mobile
- Verify ngrok URL is correct
- Check ngrok dashboard: http://localhost:4040
- Make sure you updated `backend-api.js`

### CORS errors
- Backend already has CORS enabled for all origins
- If issues persist, restart backend server

---

## Useful Commands

**View ngrok dashboard:** http://localhost:4040

**Check backend health:**
```bash
curl http://localhost:8000/health
```

**View backend logs:**
```bash
tail -f /tmp/loveai-backend.log
```

**Stop all servers:**
Press `Ctrl+C` in each terminal window

---

## Notes

- **Free ngrok URLs change** every time you restart ngrok
- For permanent URLs, upgrade to ngrok paid plan ($8/month)
- Or deploy to cloud (Render, Railway, Vercel) for permanent hosting
