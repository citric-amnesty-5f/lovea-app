# Quick Fix Instructions

## Current Issues
1. Login works but buttons don't work
2. Discovery profiles don't load
3. Mobile login doesn't work

## Root Cause
After login, `window.backendAPI.isLoggedIn()` returns false because either:
- Token isn't persisted correctly
- Profile loading is breaking something
- JavaScript error is breaking the page

## Temporary Workaround

### Desktop:
1. Clear browser cache: Cmd+Shift+Delete (Mac) or Ctrl+Shift+Delete (Windows)
2. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
3. Try logging in again

### Mobile:
1. Clear browser cache in mobile settings
2. Close and reopen browser
3. Visit: http://10.0.0.124:3000/simple-login.html
4. Login there first
5. Then navigate to http://10.0.0.124:3000

## Debug Steps
To see what's happening, visit:
- http://localhost:3000/test-api.html (desktop)
- http://10.0.0.124:3000/test-api.html (mobile)

Click "Test Full Login Flow" - if this works, the API is fine and the issue is in the main app.
