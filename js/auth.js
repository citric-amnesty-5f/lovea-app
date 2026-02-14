// Authentication Functions
async function handleLogin() {
    const email = document.getElementById('loginEmail').value.trim();
    const password = document.getElementById('loginPassword').value;
    const loginBtn = document.getElementById('loginBtn');

    if (!email || !password) {
        showAuthError('Please fill in all fields', 'auth');
        return;
    }

    // Wait for database to be initialized
    if (!datingDB) {
        showAuthError('Database is still initializing. Please wait...', 'auth');
        return;
    }

    try {
        loginBtn.disabled = true;
        loginBtn.textContent = 'Logging in...';

        console.log('Attempting to verify user:', email);
        const user = await datingDB.verifyUser(email, password);
        console.log('User verified successfully:', user);
        currentUser = user;
        
        localStorage.setItem('loveai_current_user', JSON.stringify(user));
        
        showAuthSuccess('Login successful! Redirecting...', 'auth');
        
        setTimeout(async () => {
            await showMainApp();
        }, 1000);

    } catch (error) {
        showAuthError(error.message, 'auth');
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Login';
    }
}

async function handleSignup() {
    const name = document.getElementById('signupName').value.trim();
    const email = document.getElementById('signupEmail').value.trim();
    const password = document.getElementById('signupPassword').value;
    const age = document.getElementById('signupAge').value;
    const gender = document.getElementById('signupGender').value;
    const signupBtn = document.getElementById('signupBtn');

    if (!name || !email || !password || !age || !gender) {
        showAuthError('Please fill in all fields', 'signup');
        return;
    }

    if (parseInt(age) < 18) {
        showAuthError('You must be 18 or older to create an account', 'signup');
        return;
    }

    if (password.length < 6) {
        showAuthError('Password must be at least 6 characters long', 'signup');
        return;
    }

    // Wait for database to be initialized
    if (!datingDB) {
        showAuthError('Database is still initializing. Please wait...', 'signup');
        return;
    }

    try {
        signupBtn.disabled = true;
        signupBtn.textContent = 'Creating Account...';

        const user = await datingDB.createUser({
            name, email, password, age, gender
        });

        currentUser = user;
        localStorage.setItem('loveai_current_user', JSON.stringify(user));
        
        showAuthSuccess('Account created successfully! Welcome to LoveAI!', 'signup');
        
        setTimeout(async () => {
            await showMainApp();
        }, 1500);

    } catch (error) {
        showAuthError(error.message, 'signup');
    } finally {
        signupBtn.disabled = false;
        signupBtn.textContent = 'Create Account';
    }
}

function handleLogout() {
    currentUser = null;
    localStorage.removeItem('loveai_current_user');

    document.getElementById('loginEmail').value = '';
    document.getElementById('loginPassword').value = '';

    // Stay on main app but switch to guest mode
    updateUIForAuthState();

    // Go back to discover screen
    showScreen('discover');

    showStatus('Logged out successfully - Browsing as guest');
}

function switchToSignup() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('signupForm').style.display = 'block';
    clearAuthMessages();
}

function switchToLogin() {
    document.getElementById('signupForm').style.display = 'none';
    document.getElementById('loginForm').style.display = 'block';
    clearAuthMessages();
}

// showMainApp is now in app.js