// Authentication Functions - Backend API Version
// Replaces IndexedDB with FastAPI backend

async function handleLogin() {
    const email = document.getElementById('loginEmail').value.trim().toLowerCase();
    const password = document.getElementById('loginPassword').value;
    const loginBtn = document.getElementById('loginBtn');

    if (!email || !password) {
        showAuthError('Please fill in all fields', 'auth');
        return;
    }

    try {
        loginBtn.disabled = true;
        loginBtn.textContent = 'Logging in...';

        console.log('Attempting to login:', email);

        // Use backend API instead of IndexedDB
        const result = await window.backendAPI.login(email, password);
        console.log('Login successful:', result);

        // Set current user (profile will be loaded by showMainApp)
        currentUser = {
            id: result.user_id,
            email: email,
            role: result.role,
            name: email.split('@')[0]  // Temporary name until profile loads
        };

        localStorage.setItem('loveai_current_user', JSON.stringify(currentUser));
        console.log('[handleLogin] currentUser set:', currentUser);

        showAuthSuccess('Login successful! Redirecting...', 'auth');

        setTimeout(async () => {
            console.log('[handleLogin] About to call showMainApp, currentUser:', currentUser);
            await showMainApp();
            console.log('[handleLogin] showMainApp completed, currentUser:', currentUser);
        }, 1000);

    } catch (error) {
        console.error('Login error:', error);
        showAuthError(error.message || 'Login failed. Please check your credentials.', 'auth');
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Login';
    }
}

async function handleSignup() {
    const name = document.getElementById('signupName').value.trim();
    const email = document.getElementById('signupEmail').value.trim().toLowerCase();
    const password = document.getElementById('signupPassword').value;
    const ageValue = document.getElementById('signupAge').value;
    const age = parseInt(ageValue, 10);
    const gender = document.getElementById('signupGender').value;
    const signupBtn = document.getElementById('signupBtn');

    if (!name || !email || !password || !ageValue || !gender || Number.isNaN(age)) {
        showAuthError('Please fill in all fields', 'signup');
        return;
    }

    // Calculate date of birth from age
    const today = new Date();
    const birthYear = today.getFullYear() - age;
    const dateOfBirth = `${birthYear}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;

    if (age < 18) {
        showAuthError('You must be at least 18 years old to register', 'signup');
        return;
    }

    if (password.length < 8) {
        showAuthError('Password must be at least 8 characters long', 'signup');
        return;
    }

    if (!/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/\d/.test(password)) {
        showAuthError('Password must include uppercase, lowercase, and a number.', 'signup');
        return;
    }

    try {
        signupBtn.disabled = true;
        signupBtn.textContent = 'Creating account...';

        console.log('Attempting to register:', email);

        // Use backend API instead of IndexedDB
        const userData = {
            email: email,
            password: password,
            name: name,
            date_of_birth: dateOfBirth,
            gender: gender.toLowerCase()
        };

        const result = await window.backendAPI.register(userData);
        console.log('Registration successful:', result);

        // Set current user (profile will be loaded by showMainApp)
        currentUser = {
            id: result.user_id,
            email: email,
            role: result.role
        };

        localStorage.setItem('loveai_current_user', JSON.stringify(currentUser));

        // Upload profile picture if selected
        const photoInput = document.getElementById('signupPhoto');
        if (photoInput && photoInput.files.length > 0) {
            try {
                const file = photoInput.files[0];
                if (file.size <= 5 * 1024 * 1024) {
                    const base64 = await fileToBase64(file);
                    await window.backendAPI.uploadPhoto(base64, true, 0);
                    console.log('Profile picture uploaded successfully');
                } else {
                    console.warn('Profile picture too large, skipping upload');
                }
            } catch (photoError) {
                console.error('Profile picture upload failed (non-fatal):', photoError);
            }
        }

        showAuthSuccess('Account created successfully! Redirecting...', 'signup');

        setTimeout(async () => {
            await showMainApp();
        }, 1000);

    } catch (error) {
        console.error('Registration error:', error);

        // Parse error message for better UX
        let errorMessage = error.message || 'Registration failed. Please try again.';
        if (error.message.includes('already registered')) {
            errorMessage = 'Email already registered. Please login instead.';
        } else if (error.message.includes('18 years old')) {
            errorMessage = 'You must be at least 18 years old to register.';
        } else if (error.message.includes('uppercase')) {
            errorMessage = 'Password must contain at least one uppercase letter.';
        } else if (error.message.includes('lowercase')) {
            errorMessage = 'Password must contain at least one lowercase letter.';
        } else if (error.message.includes('digit')) {
            errorMessage = 'Password must contain at least one number.';
        }

        showAuthError(errorMessage, 'signup');
    } finally {
        signupBtn.disabled = false;
        signupBtn.textContent = 'Create Account';
    }
}

async function handleLogout() {
    try {
        // Call backend logout
        await window.backendAPI.logout();

        // Disconnect WebSocket if connected
        if (window.backendAPI.ws) {
            window.backendAPI.disconnectWebSocket();
        }

        // Clear current user
        currentUser = null;
        localStorage.removeItem('loveai_current_user');

        // Hide admin controls
        const adminControls = document.getElementById('adminControls');
        if (adminControls) {
            adminControls.classList.remove('show');
        }

        // Clear any auth messages
        const authError = document.getElementById('authError');
        const authSuccess = document.getElementById('authSuccess');
        const signupError = document.getElementById('signupError');
        const signupSuccess = document.getElementById('signupSuccess');
        if (authError) authError.style.display = 'none';
        if (authSuccess) authSuccess.style.display = 'none';
        if (signupError) signupError.style.display = 'none';
        if (signupSuccess) signupSuccess.style.display = 'none';

        // Clear login form
        const loginEmail = document.getElementById('loginEmail');
        const loginPassword = document.getElementById('loginPassword');
        if (loginEmail) loginEmail.value = '';
        if (loginPassword) loginPassword.value = '';

        // Ensure login form is shown (not signup)
        const loginForm = document.getElementById('loginForm');
        const signupForm = document.getElementById('signupForm');
        if (loginForm) loginForm.style.display = 'block';
        if (signupForm) signupForm.style.display = 'none';

        // Return to auth screen
        document.getElementById('mainScreen').classList.remove('active');
        document.getElementById('authScreen').classList.add('active');

    } catch (error) {
        console.error('Logout error:', error);
        // Still log out locally even if backend call fails
        currentUser = null;
        localStorage.removeItem('loveai_current_user');
        window.backendAPI.token = null;
        window.backendAPI.currentUserId = null;

        // Hide admin controls
        const adminControls = document.getElementById('adminControls');
        if (adminControls) {
            adminControls.classList.remove('show');
        }

        // Clear any auth messages
        const authError = document.getElementById('authError');
        const authSuccess = document.getElementById('authSuccess');
        const signupError = document.getElementById('signupError');
        const signupSuccess = document.getElementById('signupSuccess');
        if (authError) authError.style.display = 'none';
        if (authSuccess) authSuccess.style.display = 'none';
        if (signupError) signupError.style.display = 'none';
        if (signupSuccess) signupSuccess.style.display = 'none';

        // Clear login form
        const loginEmail = document.getElementById('loginEmail');
        const loginPassword = document.getElementById('loginPassword');
        if (loginEmail) loginEmail.value = '';
        if (loginPassword) loginPassword.value = '';

        // Ensure login form is shown (not signup)
        const loginForm = document.getElementById('loginForm');
        const signupForm = document.getElementById('signupForm');
        if (loginForm) loginForm.style.display = 'block';
        if (signupForm) signupForm.style.display = 'none';

        document.getElementById('mainScreen').classList.remove('active');
        document.getElementById('authScreen').classList.add('active');
    }
}

// Check if user is already logged in on page load
async function checkExistingSession() {
    const savedUser = localStorage.getItem('loveai_current_user');
    const token = localStorage.getItem('auth_token');

    if (savedUser && token) {
        try {
            // Verify token is still valid
            const profile = await window.backendAPI.getMyProfile();

            currentUser = JSON.parse(savedUser);
            currentUser.profile = profile; // Update with latest profile data

            await showMainApp();
            return true;
        } catch (error) {
            console.error('Session expired:', error);
            // Clear invalid session
            localStorage.removeItem('loveai_current_user');
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_id');
            return false;
        }
    }

    return false;
}

// Helper functions for auth messages
function showAuthError(message, type) {
    const errorDiv = document.getElementById(`${type}Error`);
    const successDiv = document.getElementById(`${type}Success`);

    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }

    if (successDiv) {
        successDiv.style.display = 'none';
    }

    // Auto-hide after 5 seconds
    setTimeout(() => {
        if (errorDiv) {
            errorDiv.style.display = 'none';
        }
    }, 5000);
}

function showAuthSuccess(message, type) {
    const errorDiv = document.getElementById(`${type}Error`);
    const successDiv = document.getElementById(`${type}Success`);

    if (successDiv) {
        successDiv.textContent = message;
        successDiv.style.display = 'block';
    }

    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

// Initialize auth on page load
document.addEventListener('DOMContentLoaded', async () => {
    // Check for existing session
    const hasSession = await checkExistingSession();

    if (!hasSession) {
        // Show auth screen
        document.getElementById('authScreen').classList.add('active');
        document.getElementById('mainScreen').classList.remove('active');
    }
});
