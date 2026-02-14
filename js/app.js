// Global Variables
let datingDB = null;
let currentUser = null;
let currentProfiles = [];
let currentFilter = 'all';
let currentScreen = 'discover';

// Initialize app when page loads
async function initApp() {
    try {
        console.log('Initializing LoveAI app...');

        // Check for existing backend session
        const storedUser = localStorage.getItem('loveai_current_user');
        const authToken = localStorage.getItem('auth_token');

        if (storedUser && authToken && window.backendAPI) {
            // User has an existing session
            currentUser = JSON.parse(storedUser);
            console.log('Found existing session for:', currentUser.email);

            // Verify token is still valid by fetching profile (only if not already present)
            try {
                if (!currentUser.profile) {
                    console.log('Fetching profile for existing session...');
                    const profile = await window.backendAPI.getMyProfile();
                    currentUser.profile = profile;
                    localStorage.setItem('loveai_current_user', JSON.stringify(currentUser));
                } else {
                    console.log('Profile already loaded from storage');
                }

                // Hide auth screen and show main app
                document.getElementById('authScreen').classList.remove('active');
                document.getElementById('mainScreen').classList.add('active');

                updateUIForAuthState();
                showScreen('discover');
                console.log('Session restored successfully');
            } catch (error) {
                console.log('Session expired or invalid, showing login');
                // Session expired, clear and show login
                currentUser = null;
                localStorage.removeItem('loveai_current_user');
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user_id');
                showLoginScreen();
            }
        } else {
            // No session, show login screen
            console.log('No session found, showing login');
            showLoginScreen();
        }

    } catch (error) {
        console.error('App initialization error:', error);
        showLoginScreen();
    }
}

// Show login screen
function showLoginScreen() {
    document.getElementById('authScreen').classList.add('active');
    document.getElementById('mainScreen').classList.remove('active');

    // Hide any loading indicators
    const loadingDiv = document.getElementById('dbLoadingIndicator');
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }

    const dbStatus = document.getElementById('dbStatus');
    if (dbStatus) {
        dbStatus.style.display = 'none';
    }
}

// Function to clear database and retry
async function clearDatabaseAndRetry() {
    try {
        console.log('Clearing IndexedDB...');
        const deleteRequest = indexedDB.deleteDatabase('LoveAIDB');

        deleteRequest.onsuccess = () => {
            console.log('Database deleted successfully');
            location.reload();
        };

        deleteRequest.onerror = () => {
            console.error('Failed to delete database');
            alert('Failed to clear database. Please manually clear browser data.');
        };

        deleteRequest.onblocked = () => {
            console.warn('Delete blocked - please close other tabs');
            alert('Please close all other tabs with this site open, then try again.');
        };
    } catch (error) {
        console.error('Error clearing database:', error);
        alert('Error: ' + error.message);
    }
}

// Update UI based on authentication state
function updateUIForAuthState() {
    const welcomeEl = document.getElementById('userWelcome');
    const adminControls = document.getElementById('adminControls');
    const dbStatus = document.getElementById('dbStatus');

    // Hide the database status message
    if (dbStatus) {
        dbStatus.style.display = 'none';
    }

    if (currentUser) {
        // User is logged in
        if (welcomeEl) {
            console.log('[updateUIForAuthState] currentUser:', currentUser);
            console.log('[updateUIForAuthState] currentUser.profile:', currentUser.profile);
            console.log('[updateUIForAuthState] currentUser.profile?.name:', currentUser.profile?.name);
            console.log('[updateUIForAuthState] currentUser.email:', currentUser.email);

            const userName = currentUser.profile?.name || currentUser.name || currentUser.email?.split('@')[0] || 'User';
            const isAdmin = currentUser.role === 'admin' || currentUser.isAdmin;

            console.log('[updateUIForAuthState] userName:', userName);
            welcomeEl.innerHTML = `Welcome, ${userName}!${isAdmin ? '<span class="admin-badge">ADMIN</span>' : ''}`;
        }

        const isAdmin = currentUser.role === 'admin' || currentUser.isAdmin;
        if (adminControls) {
            if (isAdmin) {
                adminControls.classList.add('show');
            } else {
                // Regular user - hide admin controls
                adminControls.classList.remove('show');
            }
        }

        // Start notification polling
        if (typeof startNotificationPolling === 'function') {
            startNotificationPolling();
        }

        // Setup message input handler
        if (typeof setupMessageInput === 'function') {
            setupMessageInput();
        }
    } else {
        // Guest user
        if (welcomeEl) {
            welcomeEl.innerHTML = 'Guest Mode <button onclick="showLoginPrompt()" style="padding: 4px 12px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; margin-left: 8px;">Login</button>';
        }

        if (adminControls) {
            adminControls.classList.remove('show');
        }
    }
}

// Show main app after login
async function showMainApp() {
    console.log('[showMainApp] Starting - currentUser:', currentUser ? 'exists' : 'null');
    console.log('[showMainApp] Token in backendAPI:', window.backendAPI?.token ? 'exists' : 'missing');

    document.getElementById('authScreen').classList.remove('active');
    document.getElementById('mainScreen').classList.add('active');

    // Load profile if not already loaded
    if (currentUser && !currentUser.profile) {
        console.log('[showMainApp] Need to fetch profile...');

        try {
            // Double-check token is available
            if (!window.backendAPI || !window.backendAPI.token) {
                console.error('[showMainApp] ERROR: No token!');
                console.error('[showMainApp] backendAPI:', window.backendAPI);
                console.error('[showMainApp] token:', window.backendAPI?.token);
                throw new Error('Authentication token not found');
            }

            console.log('[showMainApp] Calling getMyProfile()...');
            const userProfile = await window.backendAPI.getMyProfile();
            console.log('[showMainApp] SUCCESS! Got profile:', userProfile.name);

            currentUser.profile = userProfile;
            localStorage.setItem('loveai_current_user', JSON.stringify(currentUser));
            console.log('[showMainApp] Profile saved to currentUser and localStorage');
        } catch (error) {
            console.error('[showMainApp] FAILED:', error.message);
            console.error('[showMainApp] Full error:', error);

            // Clear session and return to login
            currentUser = null;
            localStorage.removeItem('loveai_current_user');
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_id');

            showLoginScreen();

            // Show error after screen switch
            setTimeout(() => {
                if (typeof showAuthError === 'function') {
                    showAuthError('Failed to load your profile. Please try logging in again.', 'auth');
                }
            }, 100);

            return;
        }
    } else if (currentUser && currentUser.profile) {
        console.log('[showMainApp] Profile already exists:', currentUser.profile.name);
    } else {
        console.log('[showMainApp] No currentUser');
    }

    updateUIForAuthState();

    // Check if user needs onboarding (using backend API)
    if (currentUser && currentUser.profile) {
        if (!currentUser.profile.onboarding_completed) {
            // User needs onboarding
            if (typeof startOnboarding === 'function') {
                await startOnboarding();
                return;
            }
        }
    }

    // Show discover screen by default
    showScreen('discover');
}

// Show login prompt for guest users
function showLoginPrompt() {
    document.getElementById('mainScreen').classList.remove('active');
    document.getElementById('authScreen').classList.add('active');
}

// Screen navigation
function showScreen(screenName) {
    // Check if user needs to be logged in for this screen
    const authRequiredScreens = ['matches', 'messages', 'notifications'];

    if (authRequiredScreens.includes(screenName) && !currentUser) {
        showLoginRequired(`Login to access ${screenName}`);
        return;
    }

    currentScreen = screenName;

    // Hide all screens
    const screens = document.querySelectorAll('.app-screen');
    screens.forEach(screen => {
        screen.classList.remove('active');
    });

    // Update nav buttons
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.classList.remove('active');
    });

    // Show selected screen
    let screenElement;
    let navIndex;

    switch (screenName) {
        case 'discover':
            screenElement = document.getElementById('discoverScreen');
            navIndex = 0;
            loadDiscoveryProfiles();
            break;
        case 'matches':
            screenElement = document.getElementById('matchesScreenWrapper');
            navIndex = 1;
            if (typeof loadUserMatches === 'function') loadUserMatches();
            break;
        case 'messages':
            screenElement = document.getElementById('messagesScreenWrapper');
            navIndex = 2;
            if (typeof showMessagingScreen === 'function') showMessagingScreen();
            break;
        case 'notifications':
            screenElement = document.getElementById('notificationsScreen');
            navIndex = 3;
            if (typeof showNotifications === 'function') showNotifications();
            break;
        case 'settings':
            screenElement = document.getElementById('settingsScreen');
            navIndex = 4;
            if (typeof loadSettingsScreen === 'function') loadSettingsScreen();
            break;
        default:
            screenElement = document.getElementById('discoverScreen');
            navIndex = 0;
    }

    if (screenElement) {
        screenElement.classList.add('active');
    }

    if (navItems[navIndex]) {
        navItems[navIndex].classList.add('active');
    }
}

// Show login required modal (if not already defined in discovery.js)
function showLoginRequired(message) {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 400px;">
            <div class="modal-header">
                <h2>Login Required</h2>
                <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <p style="text-align: center; margin: 20px 0;">${message}</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Continue Browsing</button>
                <button class="btn btn-primary" onclick="showLoginPrompt(); this.closest('.modal').remove();">Login / Sign Up</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

// Event Listeners
window.addEventListener('load', initApp);

// Close modals when clicking outside
window.addEventListener('click', function(event) {
    if (event.target.classList.contains('modal')) {
        event.target.classList.remove('active');
        setTimeout(() => event.target.remove(), 300);
    }
});

// Handle Enter key in forms
document.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        const activeForm = document.getElementById('loginForm')?.style.display !== 'none' ? 'login' : 'signup';
        const authScreen = document.getElementById('authScreen');

        if (authScreen && authScreen.classList.contains('active')) {
            if (activeForm === 'login') {
                handleLogin();
            } else {
                handleSignup();
            }
        }
    }
});

// Utility function for status messages
function showStatus(message) {
    updateStatus(message);
    showNotificationToast(message, 'info');
}