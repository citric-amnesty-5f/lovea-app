# LoveAI - Quick Test Guide

## URLs
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## Test Credentials
```
User 1: user1@loveai.com / user123
User 2: user2@loveai.com / user123
Admin: admin@loveai.com / admin123
New User: test{random}@test.com / Test1234
```

## Quick Test Sequence (5 minutes)

### 1. Test Signup (FIXED - was broken)
1. Go to http://localhost:3000
2. Click "Sign up" link ← **NOW WORKS** (was broken)
3. Fill in:
   - Name: Test User
   - Email: test123@test.com
   - Password: Test1234
   - Age: 25
   - Gender: Male
4. Click "Create Account"
5. ✅ Should see success message
6. ✅ Should redirect to main app

### 2. Test Login
1. Logout if logged in
2. Enter: user1@loveai.com / user123
3. Click "Login"
4. ✅ Should see "Welcome, Alice!"
5. ✅ Should load main app

### 3. Test Discovery (FIXED Super Like)
1. Click "Discover" (🔍)
2. ✅ Profiles should load
3. Click ❤️ (Like) - ✅ Should work
4. Click ✕ (Pass) - ✅ Should work
5. Click ⭐ (Super Like) - **NOW WORKS** (was broken)
6. ✅ No console errors

### 4. Test Matches
1. Click "Matches" (❤️)
2. ✅ Should show matches or "No matches yet"
3. ✅ No console errors

### 5. Test Messages
1. Click "Messages" (💬)
2. ✅ Should show conversations or "No matches yet"
3. ✅ No console errors

### 6. Test Logout (FIXED - no more stale messages)
1. Click "Logout" (🚪)
2. ✅ Should return to login screen
3. ✅ Should NOT show "Login successful!" ← **FIXED**
4. ✅ Login form should be visible (not signup)

## What Was Fixed

### 🐛 Bug #1: Signup/Login Toggle Broken
**Problem:** Clicking "Sign up" or "Login" links did nothing
**Fix:** Added missing switchToSignup() and switchToLogin() functions
**Status:** ✅ FIXED

### 🐛 Bug #2: Super Like Button Error
**Problem:** Super Like crashed with "profile.id undefined"
**Fix:** Added profile validation and ID fallback
**Status:** ✅ FIXED

### 🐛 Bug #3: Logout Shows Success Message
**Problem:** After logout, login screen showed "Login successful!"
**Fix:** Clear all auth messages and reset form state
**Status:** ✅ FIXED

## Browser Console Check

Open DevTools (F12) → Console tab while testing

### ✅ Expected (Normal)
```
Initializing LoveAI app...
Found existing session for: user1@loveai.com
Session restored successfully
```

### ❌ Bad (Should NOT see after fixes)
```
switchToSignup is not defined ← FIXED
Cannot read property 'id' of undefined ← FIXED
profile.id is undefined ← FIXED
```

## Common Test Scenarios

### Scenario 1: New User Journey
1. Visit site → Click "Sign up"
2. Fill form → Create account
3. Complete onboarding (if prompted)
4. View discovery → Swipe profiles
5. Check matches → No matches yet
6. Logout → Return to login

### Scenario 2: Existing User
1. Login with user1@loveai.com
2. View discover → Like profiles
3. View matches → See existing matches
4. Open messages → Chat with matches
5. View notifications → Check alerts
6. Settings → Update preferences
7. Logout → Clean exit

### Scenario 3: Create a Match
1. Login as user1@loveai.com
2. Like a profile (e.g., Bob)
3. Logout
4. Login as user2@loveai.com
5. Like Alice's profile
6. ✅ Should see "It's a Match!" celebration
7. Can now message each other

## Files Modified
- ✅ `/Users/anilkumar/loveai-app/js/utils.js` - Added form toggle functions
- ✅ `/Users/anilkumar/loveai-app/js/discovery.js` - Fixed super like validation
- ✅ `/Users/anilkumar/loveai-app/js/auth-backend.js` - Fixed logout cleanup

## Need Help?

### Backend not running?
```bash
cd /Users/anilkumar/loveai-app/backend
uvicorn app.main:app --reload
```

### Frontend not running?
```bash
cd /Users/anilkumar/loveai-app
python3 -m http.server 3000
```

### Clear browser data
1. Open DevTools (F12)
2. Application tab
3. Clear storage → Clear site data
4. Refresh page

## Known Limitations (Not Bugs)
- Notifications endpoint not implemented yet
- Photo upload not tested
- Real-time messaging needs WebSocket
- Admin features not fully tested
