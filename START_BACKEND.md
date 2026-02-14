# Quick Start: LoveAI with Backend API

## The Issue You're Seeing

The error **"Cannot read properties of null (reading 'transaction')"** occurs because:
1. Your frontend HTML is still using IndexedDB (client-side database)
2. The new backend API is ready but not connected to the frontend yet

## Solution: Two Options

### Option 1: Start Backend + Update Frontend (Recommended)

This connects your existing frontend to the new scalable backend.

#### Step 1: Start the Backend Server

```bash
cd backend

# Set up environment (first time only)
cp .env.example .env
# Edit .env if needed

# Initialize database (first time only)
python init_db.py

# Start server
uvicorn app.main:app --reload
```

Backend will run at: **http://localhost:8000**

#### Step 2: Update Your Frontend HTML

Add this line to `index.html` BEFORE the `<script src="js/auth.js"></script>` line:

```html
<!-- Add this BEFORE auth.js -->
<script src="js/backend-api.js"></script>

<!-- Then REPLACE this line: -->
<!-- <script src="js/auth.js"></script> -->

<!-- WITH this line: -->
<script src="js/auth-backend.js"></script>
```

**Full script section should look like:**
```html
<!-- Scripts -->
<script src="js/backend-api.js"></script>  <!-- NEW -->
<!-- <script src="js/database.js"></script> --> <!-- COMMENT OUT -->
<script src="js/ai-matching.js"></script>
<script src="js/auth-backend.js"></script>  <!-- CHANGED -->
<script src="js/profiles.js"></script>
<script src="js/discovery.js"></script>
<script src="js/matches.js"></script>
<script src="js/messaging.js"></script>
<script src="js/notifications.js"></script>
<script src="js/settings.js"></script>
<script src="js/onboarding.js"></script>
<script src="js/admin.js"></script>
<script src="js/utils.js"></script>
<script src="js/app.js"></script>
```

#### Step 3: Update Gender Values in HTML

Change line 74-77 in index.html from:

```html
<option value="M">Male</option>
<option value="F">Female</option>
<option value="T">Non-binary</option>
<option value="O">Other</option>
```

To:

```html
<option value="male">Male</option>
<option value="female">Female</option>
<option value="non_binary">Non-binary</option>
<option value="other">Other</option>
```

#### Step 4: Open Frontend

```bash
# In a new terminal, from the loveai-app folder
python -m http.server 8080
```

Or use VS Code Live Server, or just open `index.html` in your browser.

Visit: **http://localhost:8080**

### Option 2: Test Backend Only (Quick Verification)

Just want to verify the backend works?

```bash
cd backend

# Start server
uvicorn app.main:app --reload

# In another terminal, test it
python test_api.py
```

Or visit the interactive docs: **http://localhost:8000/docs**

## Testing the Complete Setup

Once both backend and frontend are running:

1. **Register a new user**:
   - Email: `test@example.com`
   - Password: `TestPass123` (must have uppercase, lowercase, digit)
   - Age: 25+
   - Gender: Select one

2. **OR Login with demo account**:
   - User: `user1@loveai.com` / `user123`
   - Admin: `admin@loveai.com` / `admin123`

3. **Test the flow**:
   - ✅ View your profile
   - ✅ Update bio, occupation
   - ✅ Add interests
   - ✅ Browse discovery profiles
   - ✅ Like profiles
   - ✅ Create matches
   - ✅ Send messages
   - ✅ Logout and login again

## Troubleshooting

### Backend Not Starting?

```bash
cd backend
pip install -r requirements.txt
python init_db.py
uvicorn app.main:app --reload
```

### Still Getting Transaction Error?

1. Make sure backend is running (http://localhost:8000/health should work)
2. Check browser console for errors
3. Make sure you updated index.html with backend-api.js
4. Clear browser cache and reload

### CORS Error?

The backend allows all origins for development. If you see CORS errors:
- Make sure backend is running
- Try opening frontend via http:// not file://

## What Changed?

**Old Setup (Client-only):**
```
Frontend (HTML/JS) → IndexedDB (Browser storage)
```

**New Setup (Full-stack):**
```
Frontend (HTML/JS) → Backend API (Python/FastAPI) → PostgreSQL
```

**Benefits:**
- ✅ Real users (not just local browser data)
- ✅ AI matchmaking with GPT-4
- ✅ Real-time chat with WebSocket
- ✅ Scalable to millions of users
- ✅ Admin dashboard
- ✅ Production-ready

## Next Steps

Once working:
1. Connect more frontend features to backend API
2. Enable AI features (add OPENAI_API_KEY to .env)
3. Deploy to production
4. Add payment integration
5. Mobile apps

---

**Need Help?**
- Backend docs: `backend/README.md`
- API docs: http://localhost:8000/docs
- Tests: `cd backend && pytest tests/ -v`
