// Settings and User Profile Management

// Load settings screen
async function loadSettingsScreen() {
    const container = document.getElementById('settingsContainer');
    if (!container) return;

    // Guest user view
    if (!currentUser) {
        container.innerHTML = `
            <div class="settings-sections">
                <div class="settings-section" style="text-align: center; padding: 40px 20px;">
                    <div style="font-size: 48px; margin-bottom: 20px;">👤</div>
                    <h3>Guest Mode</h3>
                    <p style="color: #666; margin: 20px 0;">
                        You're browsing as a guest. Login or create an account to:
                    </p>
                    <ul style="text-align: left; max-width: 300px; margin: 20px auto; color: #666;">
                        <li>Like profiles and get matches</li>
                        <li>Send and receive messages</li>
                        <li>Get AI-powered compatibility scores</li>
                        <li>Customize your preferences</li>
                        <li>Save your favorite profiles</li>
                    </ul>
                    <div style="margin-top: 30px;">
                        <button class="btn btn-primary" onclick="showLoginPrompt()" style="margin-right: 10px;">
                            Login
                        </button>
                        <button class="btn btn-secondary" onclick="switchToSignupAndShow()">
                            Sign Up
                        </button>
                    </div>
                </div>
            </div>
        `;
        return;
    }

    // Logged-in user view
    try {
        // Use backend API
        let preferences = null;
        let userProfile = null;

        if (window.backendAPI && window.backendAPI.isLoggedIn()) {
            userProfile = await window.backendAPI.getMyProfile();
            try {
                preferences = await window.backendAPI.getPreferences();
            } catch (error) {
                console.log('No preferences found, using defaults');
                preferences = null;
            }
        } else if (typeof datingDB !== 'undefined') {
            // Fallback to local database
            preferences = await datingDB.getUserPreferences(currentUser.id);
            userProfile = await datingDB.getUserProfile(currentUser.id);
        }

        displaySettingsForm(preferences, userProfile);
    } catch (error) {
        console.error('Error loading settings:', error);
        showStatus('Error loading settings');
    }
}

// Helper to switch to signup form and show it
function switchToSignupAndShow() {
    showLoginPrompt();
    setTimeout(() => {
        switchToSignup();
    }, 100);
}

function displaySettingsForm(preferences, userProfile) {
    const container = document.getElementById('settingsContainer');
    if (!container) return;

    container.innerHTML = `
        <div class="settings-sections">
            <!-- Profile Section -->
            <div class="settings-section">
                <h3>My Profile</h3>
                <div class="profile-preview">
                    <div class="profile-avatar-large">${userProfile?.avatar || '👤'}</div>
                    <button class="btn btn-secondary" onclick="editProfile()">Edit Profile</button>
                </div>
            </div>

            <!-- AI Settings -->
            <div class="settings-section">
                <h3>AI Settings</h3>
                <div class="form-group">
                    <label>OpenAI API Key</label>
                    <input type="password" id="apiKeyInput"
                           value="${aiEngine.getApiKey() || ''}"
                           placeholder="sk-...">
                    <small>Enter your OpenAI API key for AI-powered matching</small>
                </div>
                <button class="btn btn-primary" onclick="saveApiKey()">Save API Key</button>
                <button class="btn btn-secondary" onclick="testApiKey()">Test Connection</button>
            </div>

            <!-- Preferences Section -->
            <div class="settings-section">
                <h3>Discovery Preferences</h3>

                <div class="form-group">
                    <label>Age Range: ${preferences.ageMin} - ${preferences.ageMax}</label>
                    <div class="range-inputs">
                        <input type="number" id="ageMin" value="${preferences.ageMin}" min="18" max="100">
                        <span>to</span>
                        <input type="number" id="ageMax" value="${preferences.ageMax}" min="18" max="100">
                    </div>
                </div>

                <div class="form-group">
                    <label>Maximum Distance (miles)</label>
                    <input type="range" id="maxDistance" value="${preferences.maxDistance}"
                           min="1" max="100" oninput="updateDistanceLabel(this.value)">
                    <span id="distanceLabel">${preferences.maxDistance} miles</span>
                </div>

                <div class="form-group">
                    <label>Show Me</label>
                    <select id="genderPreference">
                        <option value="all" ${preferences.genderPreference === 'all' ? 'selected' : ''}>Everyone</option>
                        <option value="M" ${preferences.genderPreference === 'M' ? 'selected' : ''}>Men</option>
                        <option value="F" ${preferences.genderPreference === 'F' ? 'selected' : ''}>Women</option>
                        <option value="T" ${preferences.genderPreference === 'T' ? 'selected' : ''}>Non-binary</option>
                    </select>
                </div>

                <div class="form-group">
                    <label class="checkbox-label">
                        <input type="checkbox" id="showMe" ${preferences.showMe ? 'checked' : ''}>
                        Show my profile in discovery
                    </label>
                </div>
            </div>

            <!-- Notifications Section -->
            <div class="settings-section">
                <h3>Notifications</h3>

                <div class="form-group">
                    <label class="checkbox-label">
                        <input type="checkbox" id="notifyMatches"
                               ${preferences.notifications?.matches ? 'checked' : ''}>
                        New matches
                    </label>
                </div>

                <div class="form-group">
                    <label class="checkbox-label">
                        <input type="checkbox" id="notifyMessages"
                               ${preferences.notifications?.messages ? 'checked' : ''}>
                        New messages
                    </label>
                </div>

                <div class="form-group">
                    <label class="checkbox-label">
                        <input type="checkbox" id="notifyLikes"
                               ${preferences.notifications?.likes !== false ? 'checked' : ''}>
                        Someone liked you
                    </label>
                </div>
            </div>

            <!-- Safety Section -->
            <div class="settings-section">
                <h3>Safety & Privacy</h3>
                <button class="btn btn-secondary" onclick="viewBlockedUsers()">Blocked Users</button>
                <button class="btn btn-secondary" onclick="showSafetyTips()">Safety Tips</button>
            </div>

            <!-- Account Section -->
            <div class="settings-section">
                <h3>Account</h3>
                <button class="btn btn-secondary" onclick="changePassword()">Change Password</button>
                <button class="btn btn-danger" onclick="confirmDeleteAccount()">Delete Account</button>
            </div>

            <!-- Save Button -->
            <div class="settings-actions">
                <button class="btn btn-primary btn-large" onclick="saveSettings()">Save Preferences</button>
            </div>
        </div>
    `;
}

function updateDistanceLabel(value) {
    document.getElementById('distanceLabel').textContent = value + ' miles';
}

async function saveApiKey() {
    const apiKey = document.getElementById('apiKeyInput').value.trim();

    if (!apiKey) {
        showStatus('Please enter an API key');
        return;
    }

    aiEngine.setApiKey(apiKey);
    showStatus('API key saved successfully!');
}

async function testApiKey() {
    try {
        showStatus('Testing API connection...');

        const messages = [
            { role: 'user', content: 'Say "API connection successful" if you can read this.' }
        ];

        const response = await aiEngine.callChatGPT(messages, 0.5);

        if (response) {
            showStatus('✓ API connection successful!');
        }
    } catch (error) {
        showStatus('✗ API connection failed: ' + error.message);
    }
}

async function saveSettings() {
    try {
        const preferences = {
            ageMin: parseInt(document.getElementById('ageMin').value),
            ageMax: parseInt(document.getElementById('ageMax').value),
            maxDistance: parseInt(document.getElementById('maxDistance').value),
            genderPreference: document.getElementById('genderPreference').value,
            showMe: document.getElementById('showMe').checked,
            notifications: {
                matches: document.getElementById('notifyMatches').checked,
                messages: document.getElementById('notifyMessages').checked,
                likes: document.getElementById('notifyLikes').checked
            }
        };

        await datingDB.saveUserPreferences(currentUser.id, preferences);
        showStatus('Preferences saved successfully!');
    } catch (error) {
        console.error('Error saving preferences:', error);
        showStatus('Error saving preferences');
    }
}

async function editProfile() {
    const userProfile = await datingDB.getUserProfile(currentUser.id);

    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.id = 'editProfileModal';

    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Edit Profile</h2>
                <button class="close-btn" onclick="closeEditProfileModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Avatar Emoji</label>
                    <input type="text" id="profileAvatar" value="${userProfile?.avatar || '👤'}"
                           maxlength="2" placeholder="👤">
                </div>

                <div class="form-group">
                    <label>Bio</label>
                    <textarea id="profileBio" rows="4" placeholder="Tell people about yourself...">${userProfile?.bio || ''}</textarea>
                    ${aiEngine.hasApiKey() ? '<button class="btn btn-sm" onclick="generateBio()">✨ AI Suggestions</button>' : ''}
                </div>

                <div class="form-group">
                    <label>Occupation</label>
                    <input type="text" id="profileOccupation" value="${userProfile?.occupation || ''}"
                           placeholder="What do you do?">
                </div>

                <div class="form-group">
                    <label>Location</label>
                    <input type="text" id="profileLocation" value="${userProfile?.location || ''}"
                           placeholder="City, State">
                </div>

                <div class="form-group">
                    <label>Interests (comma separated)</label>
                    <input type="text" id="profileInterests"
                           value="${userProfile?.interests?.join(', ') || ''}"
                           placeholder="hiking, cooking, music">
                </div>

                <div class="form-group">
                    <label>Photos</label>
                    <input type="file" id="profilePhotos" accept="image/*" multiple>
                    <small>Select up to 6 photos</small>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="closeEditProfileModal()">Cancel</button>
                <button class="btn btn-primary" onclick="saveProfile()">Save Profile</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

function closeEditProfileModal() {
    const modal = document.getElementById('editProfileModal');
    if (modal) modal.remove();
}

async function generateBio() {
    try {
        showStatus('Generating bio suggestions...');

        const userInfo = {
            name: currentUser.name,
            age: currentUser.age,
            occupation: document.getElementById('profileOccupation').value,
            interests: document.getElementById('profileInterests').value.split(',').map(i => i.trim())
        };

        const suggestions = await aiEngine.generateBioSuggestions(userInfo);

        // Show suggestions in a popup
        const suggestionsDiv = document.createElement('div');
        suggestionsDiv.className = 'bio-suggestions';
        suggestionsDiv.innerHTML = '<h4>AI Bio Suggestions:</h4>';

        suggestions.forEach((bio, index) => {
            const btn = document.createElement('button');
            btn.className = 'suggestion-btn';
            btn.textContent = bio;
            btn.onclick = () => {
                document.getElementById('profileBio').value = bio;
                suggestionsDiv.remove();
            };
            suggestionsDiv.appendChild(btn);
        });

        document.querySelector('.modal-body').appendChild(suggestionsDiv);
        showStatus('');
    } catch (error) {
        showStatus('Failed to generate suggestions: ' + error.message);
    }
}

async function saveProfile() {
    try {
        const avatar = document.getElementById('profileAvatar').value || '👤';
        const bio = document.getElementById('profileBio').value.trim();
        const occupation = document.getElementById('profileOccupation').value.trim();
        const location = document.getElementById('profileLocation').value.trim();
        const interests = document.getElementById('profileInterests').value
            .split(',')
            .map(i => i.trim())
            .filter(i => i);

        // Handle photo uploads
        const photos = await handlePhotoUploads();

        const profileData = {
            userId: currentUser.id,
            name: currentUser.name,
            age: currentUser.age,
            gender: currentUser.gender,
            avatar,
            bio,
            occupation,
            location,
            interests,
            photos
        };

        const existingProfile = await datingDB.getUserProfile(currentUser.id);

        if (existingProfile) {
            await datingDB.updateUserProfile(existingProfile.id, profileData);
        } else {
            await datingDB.createUserProfile(profileData);
        }

        showStatus('Profile saved successfully!');
        closeEditProfileModal();
        loadSettingsScreen();
    } catch (error) {
        console.error('Error saving profile:', error);
        showStatus('Error saving profile');
    }
}

async function handlePhotoUploads() {
    const fileInput = document.getElementById('profilePhotos');
    const files = fileInput.files;

    if (files.length === 0) return [];

    const photos = [];
    const maxPhotos = Math.min(files.length, 6);

    for (let i = 0; i < maxPhotos; i++) {
        const file = files[i];

        if (file.size > 5 * 1024 * 1024) {
            showStatus('Photo ' + (i + 1) + ' is too large. Max 5MB.');
            continue;
        }

        const base64 = await fileToBase64(file);
        photos.push({
            id: 'photo_' + Date.now() + '_' + i,
            data: base64,
            primary: i === 0
        });
    }

    return photos;
}

function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

async function viewBlockedUsers() {
    try {
        const blocked = await datingDB.getBlockedUsers(currentUser.id);

        const modal = document.createElement('div');
        modal.className = 'modal active';
        modal.id = 'blockedUsersModal';

        let content = '<h3>Blocked Users</h3>';

        if (blocked.length === 0) {
            content += '<p class="empty-state">No blocked users</p>';
        } else {
            content += '<div class="blocked-users-list">';
            for (const block of blocked) {
                const user = await datingDB.promisifyRequest(
                    datingDB.db.transaction(['users'], 'readonly').objectStore('users').get(block.blockedUserId)
                );

                content += `
                    <div class="blocked-user-item">
                        <span>${user?.name || 'Unknown'}</span>
                        <button class="btn btn-sm" onclick="unblockUser('${block.blockedUserId}')">Unblock</button>
                    </div>
                `;
            }
            content += '</div>';
        }

        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
                </div>
                <div class="modal-body">${content}</div>
            </div>
        `;

        document.body.appendChild(modal);
    } catch (error) {
        console.error('Error loading blocked users:', error);
    }
}

async function unblockUser(userId) {
    try {
        await datingDB.unblockUser(currentUser.id, userId);
        showStatus('User unblocked');
        document.getElementById('blockedUsersModal')?.remove();
        viewBlockedUsers();
    } catch (error) {
        console.error('Error unblocking user:', error);
        showStatus('Error unblocking user');
    }
}

function showSafetyTips() {
    const modal = document.createElement('div');
    modal.className = 'modal active';

    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Safety Tips</h2>
                <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="safety-tips">
                    <h4>🛡️ Stay Safe While Dating</h4>
                    <ul>
                        <li>Never share personal information too quickly</li>
                        <li>Meet in public places for first dates</li>
                        <li>Tell a friend where you're going</li>
                        <li>Trust your instincts - if something feels off, it probably is</li>
                        <li>Don't send money to people you haven't met in person</li>
                        <li>Video chat before meeting in person</li>
                        <li>Report suspicious behavior immediately</li>
                        <li>Keep conversations on the app initially</li>
                    </ul>
                    <p>Your safety is our priority. If you encounter any concerning behavior, use the report feature.</p>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

function changePassword() {
    const modal = document.createElement('div');
    modal.className = 'modal active';

    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Change Password</h2>
                <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Current Password</label>
                    <input type="password" id="currentPassword">
                </div>
                <div class="form-group">
                    <label>New Password</label>
                    <input type="password" id="newPassword" minlength="6">
                </div>
                <div class="form-group">
                    <label>Confirm New Password</label>
                    <input type="password" id="confirmPassword" minlength="6">
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                <button class="btn btn-primary" onclick="submitPasswordChange()">Change Password</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

async function submitPasswordChange() {
    const current = document.getElementById('currentPassword').value;
    const newPass = document.getElementById('newPassword').value;
    const confirm = document.getElementById('confirmPassword').value;

    if (!current || !newPass || !confirm) {
        showStatus('Please fill all fields');
        return;
    }

    if (newPass !== confirm) {
        showStatus('New passwords do not match');
        return;
    }

    if (newPass.length < 6) {
        showStatus('Password must be at least 6 characters');
        return;
    }

    try {
        // Verify current password
        await datingDB.verifyUser(currentUser.email, current);

        // Update password
        const hashedPassword = await datingDB.hashPassword(newPass);
        currentUser.password = hashedPassword;

        const transaction = datingDB.db.transaction(['users'], 'readwrite');
        const store = transaction.objectStore('users');
        await datingDB.promisifyRequest(store.put(currentUser));

        showStatus('Password changed successfully!');
        document.querySelector('.modal').remove();
    } catch (error) {
        showStatus('Current password is incorrect');
    }
}

function confirmDeleteAccount() {
    if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
        deleteAccount();
    }
}

async function deleteAccount() {
    try {
        // Delete user data
        const transaction = datingDB.db.transaction(['users'], 'readwrite');
        const store = transaction.objectStore('users');
        await datingDB.promisifyRequest(store.delete(currentUser.id));

        // Delete profile
        const userProfile = await datingDB.getUserProfile(currentUser.id);
        if (userProfile) {
            const profileTx = datingDB.db.transaction(['profiles'], 'readwrite');
            await datingDB.promisifyRequest(profileTx.objectStore('profiles').delete(userProfile.id));
        }

        // Log out
        handleLogout();
        showStatus('Account deleted successfully');
    } catch (error) {
        console.error('Error deleting account:', error);
        showStatus('Error deleting account');
    }
}
