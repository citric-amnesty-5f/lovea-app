# LoveAI - Quick Start Guide

## 🚀 Getting Started (30 seconds)

### Step 1: Refresh Browser
**IMPORTANT**: Hard refresh to load updated JavaScript files

- **Mac**: Press `Cmd + Shift + R`
- **Windows/Linux**: Press `Ctrl + Shift + R`

### Step 2: You Should See
✅ **Login Screen** with email/password fields
❌ **NOT** "Initializing database..." stuck screen

### Step 3: Login
Use any demo account:
```
Email: user1@loveai.com
Password: user123
```

Or try users 2-20:
- user2@loveai.com / user123
- user3@loveai.com / user123
- ... up to user20@loveai.com / user123

Admin account:
```
Email: admin@loveai.com
Password: admin123
```

### Step 4: Start Swiping!
After login, you'll see profiles automatically.
- **Swipe Right** ❤️ = Like
- **Swipe Left** ✕ = Pass
- **Click Star** ⭐ = Super Like

---

## 🎯 Testing Match Feature

### Create a Match
1. **First tab**: Login as user1@loveai.com
2. Like a profile (e.g., Frank - user7)
3. **Second tab/incognito**: Login as user6@loveai.com
4. Like user1 back
5. **Result**: "It's a Match!" celebration 🎉

---

## 🔧 Services Running

| Service | URL | Status |
|---------|-----|--------|
| Frontend | http://localhost:3000 | ✅ Running |
| Backend API | http://localhost:8000 | ✅ Running |
| API Docs | http://localhost:8000/docs | ✅ Running |

---

## 📊 Test Accounts

| Email | Password | Name | Age | Gender |
|-------|----------|------|-----|--------|
| user1@loveai.com | user123 | Alice | 41 | Male |
| user2@loveai.com | user123 | Bob | 39 | Non-Binary |
| user3@loveai.com | user123 | Charlie | 36 | Male |
| user4@loveai.com | user123 | Diana | 32 | Non-Binary |
| user5@loveai.com | user123 | Eve | 27 | Female |
| user6@loveai.com | user123 | Frank | 43 | Male |
| ... | user123 | ... | ... | ... |

---

## ✨ Features to Test

### Discovery
- [x] Browse profiles
- [x] See bio, occupation, interests
- [x] AI compatibility scores
- [x] Swipe gestures

### Interactions
- [x] Like profiles
- [x] Pass on profiles
- [x] Super like
- [x] Match creation

### Matching
- [x] View matches
- [x] See compatibility reasons
- [x] AI-generated ice breakers
- [x] Match celebration modal

### Profile
- [x] View your profile
- [x] Edit bio
- [x] Add/remove interests
- [x] Update preferences

### Settings
- [x] Update age range preference
- [x] Update gender preference
- [x] Update distance preference
- [x] Privacy settings

---

## 🐛 Troubleshooting

### Issue: Still seeing "Initializing database..."
**Fix**: Clear browser cache and hard refresh
```
1. Press F12 (Developer Tools)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"
```

### Issue: Login fails
**Check**:
1. Backend running? `curl http://localhost:8000/health`
2. Correct credentials? user1@loveai.com / user123
3. Check console (F12) for error messages

### Issue: Discovery shows no profiles
**Check**:
1. Are you logged in? (Check top-right corner)
2. Backend has data? `curl -H "Authorization: Bearer TOKEN" http://localhost:8000/discovery/profiles`
3. Console errors? (F12)

### Issue: Can't click/swipe
**Fix**: Make sure you're logged in first. Some features require authentication.

---

## 💡 Pro Tips

### Test Multiple Users
Open incognito/private windows to test multiple users simultaneously:
- **Regular window**: user1@loveai.com
- **Incognito window**: user6@loveai.com
- Like each other → Create match!

### View Backend Logs
```bash
# See real-time backend activity
tail -f /private/tmp/claude-501/-Users-anilkumar-loveai-app/tasks/bd71016.output
```

### Test API Directly
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user1@loveai.com","password":"user123"}'

# Get profiles (replace TOKEN with actual token)
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/discovery/profiles
```

### Clear Session
To test fresh login:
```javascript
// In browser console (F12)
localStorage.clear()
location.reload()
```

---

## 📚 Documentation

- **INITIALIZATION_FIX.md** - How app startup was fixed
- **DISCOVERY_FIX.md** - How discovery feature was fixed
- **TEST_RESULTS.md** - Full test results
- **backend/README.md** - Backend API documentation

---

## 🎊 You're Ready!

Just **refresh your browser** and start using the app!

**Default Flow**:
1. Open app → Login screen
2. Login → Discovery screen
3. Start swiping! 💕

---

**Need Help?** Check console (F12) for error messages and refer to troubleshooting section above.

**Happy Swiping! 🎉**
