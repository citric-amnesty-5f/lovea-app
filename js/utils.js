// Utility Functions
function updateStatus(message) {
    const statusEl = document.getElementById('dbStatus');
    statusEl.textContent = message;
}

function showAuthError(message, form) {
    const errorEl = document.getElementById(form + 'Error');
    const successEl = document.getElementById(form + 'Success');
    
    errorEl.textContent = message;
    errorEl.style.display = 'block';
    successEl.style.display = 'none';
}

function showAuthSuccess(message, form) {
    const errorEl = document.getElementById(form + 'Error');
    const successEl = document.getElementById(form + 'Success');
    
    successEl.textContent = message;
    successEl.style.display = 'block';
    errorEl.style.display = 'none';
}

function clearAuthMessages() {
    ['auth', 'signup'].forEach(form => {
        document.getElementById(form + 'Error').style.display = 'none';
        document.getElementById(form + 'Success').style.display = 'none';
    });
}

// Switch between login and signup forms
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