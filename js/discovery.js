// Swipe-based Discovery Interface

let discoveryProfiles = [];
let currentProfileIndex = 0;
let swipeStartX = 0;
let swipeStartY = 0;
let isDragging = false;

// Load discovery profiles
async function loadDiscoveryProfiles() {
    console.log('[loadDiscoveryProfiles] Starting...');
    console.log('[loadDiscoveryProfiles] backendAPI:', !!window.backendAPI);
    console.log('[loadDiscoveryProfiles] isLoggedIn:', window.backendAPI?.isLoggedIn());

    try {
        // Use backend API
        if (window.backendAPI && window.backendAPI.isLoggedIn()) {
            console.log('[loadDiscoveryProfiles] Calling getDiscoveryProfiles...');
            // Load profiles from backend
            discoveryProfiles = await window.backendAPI.getDiscoveryProfiles(20);
            console.log('[loadDiscoveryProfiles] Received', discoveryProfiles.length, 'profiles');

            // Backend already filters by preferences, so we just need to transform the data
            discoveryProfiles = discoveryProfiles.map(profile => ({
                ...profile,
                userId: profile.id,
                aiCompatibility: profile.ai_compatibility_score,
                compatibilityReason: profile.ai_compatibility_reasons?.[0],
                compatibilityHighlights: profile.ai_compatibility_reasons || [],
                compatibilityConcerns: []
            }));
        } else {
            console.warn('[loadDiscoveryProfiles] Not logged in or backendAPI missing');
            console.warn('[loadDiscoveryProfiles] backendAPI:', window.backendAPI);
            console.warn('[loadDiscoveryProfiles] token:', window.backendAPI?.token);
            console.warn('[loadDiscoveryProfiles] currentUserId:', window.backendAPI?.currentUserId);
            console.warn('[loadDiscoveryProfiles] localStorage auth_token:', localStorage.getItem('auth_token'));
            console.warn('[loadDiscoveryProfiles] localStorage user_id:', localStorage.getItem('user_id'));

            // Guest mode - use old method if datingDB exists
            if (typeof datingDB !== 'undefined') {
                const allProfiles = await datingDB.getAllProfiles();
                discoveryProfiles = allProfiles;
            } else {
                console.warn('Not logged in and no local database available');

                // Show visible warning that user appears logged in but isLoggedIn() is false
                const container = document.getElementById('swipeCard');
                if (container && localStorage.getItem('auth_token')) {
                    container.innerHTML = `
                        <div style="text-align: center; padding: 40px; background: rgba(251, 191, 36, 0.2); border-radius: 16px; margin: 20px;">
                            <div style="font-size: 48px; margin-bottom: 20px;">⚠️</div>
                            <div style="font-size: 20px; font-weight: bold; margin-bottom: 10px;">Session Error</div>
                            <div style="font-size: 14px; opacity: 0.9; margin-bottom: 10px;">You appear to be logged in, but the session is invalid.</div>
                            <div style="font-size: 12px; opacity: 0.7; margin-bottom: 20px;">
                                Debug info:<br>
                                Token in localStorage: ${!!localStorage.getItem('auth_token')}<br>
                                Token in backendAPI: ${!!window.backendAPI?.token}<br>
                                User ID: ${localStorage.getItem('user_id') || 'null'}<br>
                                isLoggedIn(): ${window.backendAPI?.isLoggedIn()}
                            </div>
                            <button onclick="location.reload()" style="margin-top: 20px; padding: 12px 24px; background: white; color: #667eea; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">Reload Page</button>
                        </div>
                    `;
                }

                discoveryProfiles = [];
            }
        }

        currentProfileIndex = 0;

        if (discoveryProfiles.length === 0) {
            console.log('[loadDiscoveryProfiles] No profiles, showing message');
            showNoProfilesMessage();
        } else {
            console.log('[loadDiscoveryProfiles] Showing first profile');
            showCurrentProfile();
        }
    } catch (error) {
        console.error('[loadDiscoveryProfiles] ERROR:', error);
        console.error('[loadDiscoveryProfiles] Error message:', error.message);
        console.error('[loadDiscoveryProfiles] Error stack:', error.stack);

        // Show visible error message
        const container = document.getElementById('swipeCard');
        if (container) {
            container.innerHTML = `
                <div style="text-align: center; padding: 40px; background: rgba(239, 68, 68, 0.2); border-radius: 16px; margin: 20px;">
                    <div style="font-size: 48px; margin-bottom: 20px;">❌</div>
                    <div style="font-size: 20px; font-weight: bold; margin-bottom: 10px;">Error Loading Profiles</div>
                    <div style="font-size: 14px; opacity: 0.9;">${error.message}</div>
                    <div style="margin-top: 20px; font-size: 12px; opacity: 0.7;">Check browser console for details</div>
                    <button onclick="location.reload()" style="margin-top: 20px; padding: 12px 24px; background: white; color: #667eea; border: none; border-radius: 8px; font-weight: bold; cursor: pointer;">Reload Page</button>
                </div>
            `;
        }

        showStatus('Error loading profiles: ' + error.message);
    }
}

function showCurrentProfile() {
    if (currentProfileIndex >= discoveryProfiles.length) {
        showNoProfilesMessage();
        return;
    }

    const profile = discoveryProfiles[currentProfileIndex];
    const container = document.getElementById('swipeCard');

    if (!container) return;

    container.style.transform = 'translateX(0) rotate(0deg)';
    container.style.opacity = '1';

    const primaryPhoto = profile.photos?.[0]?.data || null;

    container.innerHTML = `
        <div class="swipe-card-inner">
            ${primaryPhoto ?
            `<img src="${primaryPhoto}" class="swipe-card-image" alt="${profile.name}">` :
            `<div class="swipe-card-avatar">${profile.avatar || '👤'}</div>`
        }
            <div class="swipe-card-overlay"></div>
            <div class="swipe-card-info">
                <div class="swipe-card-name">${profile.name}, ${profile.age}</div>
                <div class="swipe-card-location">📍 ${profile.location || 'Unknown'}</div>
                <div class="swipe-card-occupation">${profile.occupation || ''}</div>

                ${profile.aiCompatibility ?
            `<div class="swipe-card-match">${profile.aiCompatibility}% Match</div>` : ''
        }
            </div>

            <div class="swipe-indicators">
                <div class="swipe-indicator swipe-nope">PASS</div>
                <div class="swipe-indicator swipe-like">LIKE</div>
            </div>
        </div>
    `;

    // Update profile details section
    updateProfileDetails(profile);

    // Setup swipe handlers
    setupSwipeHandlers(container);
}

function updateProfileDetails(profile) {
    const detailsContainer = document.getElementById('profileDetailsContainer');
    if (!detailsContainer) return;

    detailsContainer.innerHTML = `
        <div class="profile-details-section">
            <h4>About ${profile.name}</h4>
            <p>${profile.bio || 'No bio available'}</p>
        </div>

        ${profile.interests && profile.interests.length > 0 ? `
            <div class="profile-details-section">
                <h4>Interests</h4>
                <div class="interests-tags">
                    ${profile.interests.map(interest => {
                        const interestName = typeof interest === 'string' ? interest : (interest.name || interest);
                        const interestIcon = interest.icon || '';
                        return `<span class="interest-tag">${interestIcon} ${interestName}</span>`;
                    }).join('')}
                </div>
            </div>
        ` : ''}

        ${profile.compatibilityHighlights && profile.compatibilityHighlights.length > 0 ? `
            <div class="profile-details-section">
                <h4>✨ Why you might match</h4>
                <ul class="compatibility-list">
                    ${profile.compatibilityHighlights.map(h =>
        `<li>${h}</li>`
    ).join('')}
                </ul>
            </div>
        ` : ''}

        ${profile.photos && profile.photos.length > 1 ? `
            <div class="profile-details-section">
                <h4>Photos</h4>
                <div class="profile-photos-grid">
                    ${profile.photos.map((photo, index) =>
        `<img src="${photo.data}" class="profile-photo-thumb" alt="Photo ${index + 1}">`
    ).join('')}
                </div>
            </div>
        ` : ''}

        <div class="profile-details-section">
            <button class="btn btn-danger btn-sm" onclick="reportCurrentProfile()">Report</button>
        </div>
    `;
}

function setupSwipeHandlers(card) {
    // Mouse/Touch handlers
    card.addEventListener('mousedown', handleSwipeStart);
    card.addEventListener('touchstart', handleSwipeStart);

    document.addEventListener('mousemove', handleSwipeMove);
    document.addEventListener('touchmove', handleSwipeMove);

    document.addEventListener('mouseup', handleSwipeEnd);
    document.addEventListener('touchend', handleSwipeEnd);
}

function handleSwipeStart(e) {
    isDragging = true;
    const touch = e.touches ? e.touches[0] : e;
    swipeStartX = touch.clientX;
    swipeStartY = touch.clientY;
}

function handleSwipeMove(e) {
    if (!isDragging) return;

    const touch = e.touches ? e.touches[0] : e;
    const deltaX = touch.clientX - swipeStartX;
    const deltaY = touch.clientY - swipeStartY;

    const card = document.getElementById('swipeCard');
    if (!card) return;

    const rotation = deltaX / 20;

    card.style.transform = `translateX(${deltaX}px) translateY(${deltaY}px) rotate(${rotation}deg)`;

    // Show indicators
    const likeIndicator = card.querySelector('.swipe-like');
    const nopeIndicator = card.querySelector('.swipe-nope');

    if (deltaX > 50) {
        likeIndicator.style.opacity = Math.min(deltaX / 100, 1);
        nopeIndicator.style.opacity = 0;
    } else if (deltaX < -50) {
        nopeIndicator.style.opacity = Math.min(Math.abs(deltaX) / 100, 1);
        likeIndicator.style.opacity = 0;
    } else {
        likeIndicator.style.opacity = 0;
        nopeIndicator.style.opacity = 0;
    }
}

async function handleSwipeEnd(e) {
    if (!isDragging) return;
    isDragging = false;

    const touch = e.changedTouches ? e.changedTouches[0] : e;
    const deltaX = touch.clientX - swipeStartX;

    const card = document.getElementById('swipeCard');
    if (!card) return;

    const threshold = 100;

    if (deltaX > threshold) {
        // Swipe right (like)
        await animateSwipe(card, 'like');
        await handleSwipeAction('like');
    } else if (deltaX < -threshold) {
        // Swipe left (pass)
        await animateSwipe(card, 'pass');
        await handleSwipeAction('pass');
    } else {
        // Return to center
        card.style.transform = 'translateX(0) rotate(0deg)';
        card.querySelector('.swipe-like').style.opacity = 0;
        card.querySelector('.swipe-nope').style.opacity = 0;
    }
}

function animateSwipe(card, direction) {
    return new Promise(resolve => {
        const distance = direction === 'like' ? 1000 : -1000;
        card.style.transition = 'transform 0.3s ease-out, opacity 0.3s ease-out';
        card.style.transform = `translateX(${distance}px) rotate(${distance / 10}deg)`;
        card.style.opacity = '0';

        setTimeout(() => {
            card.style.transition = '';
            resolve();
        }, 300);
    });
}

async function handleSwipeAction(action) {
    const profile = discoveryProfiles[currentProfileIndex];

    // Check if profile exists
    if (!profile) {
        console.error('No profile at index:', currentProfileIndex);
        showStatus('No profile available');
        return;
    }

    // Require login for actions
    if (!currentUser) {
        showLoginRequired('You need to login to like or pass on profiles');
        return;
    }

    try {
        // Record interaction using backend API
        if (window.backendAPI && window.backendAPI.isLoggedIn()) {
            const profileId = profile.id || profile.userId;
            if (!profileId) {
                console.error('Profile has no ID:', profile);
                showStatus('Error: Profile has no ID');
                return;
            }
            const result = await window.backendAPI.createInteraction(profileId, action);

            if (action === 'like' && result.is_match) {
                // Show match celebration
                await celebrateMatch(profile, result.match_id);
            } else if (action === 'like') {
                showStatus(`You liked ${profile.name}!`);
            }
        } else if (typeof datingDB !== 'undefined') {
            // Fallback to local database
            await datingDB.addInteraction(currentUser.id, profile.id, action);

            if (action === 'like') {
                const match = await checkAndCelebrateMatch(currentUser.id, profile.id);
                if (!match) {
                    showStatus(`You liked ${profile.name}!`);
                }
            }
        }

        // Move to next profile
        currentProfileIndex++;
        showCurrentProfile();

        // Update insights
        if (typeof updateAIInsights === 'function') {
            updateAIInsights();
        }
    } catch (error) {
        console.error('Error handling swipe:', error);
        showStatus(`Error: ${error.message || 'Error processing swipe'}`);
    }
}

function showNoProfilesMessage() {
    const container = document.getElementById('swipeCard');
    if (!container) return;

    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <h3>No More Profiles</h3>
            <p>You've seen everyone! Check back later for new matches.</p>
            <button class="btn btn-primary" onclick="loadDiscoveryProfiles()">Refresh</button>
        </div>
    `;
}

// Show login required modal
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

// Button actions for swipe
async function swipeLeft() {
    if (!currentUser) {
        showLoginRequired('Login to pass on profiles');
        return;
    }

    const card = document.getElementById('swipeCard');
    if (!card) return;

    await animateSwipe(card, 'pass');
    await handleSwipeAction('pass');
}

async function swipeRight() {
    if (!currentUser) {
        showLoginRequired('Login to like profiles and create matches!');
        return;
    }

    const card = document.getElementById('swipeCard');
    if (!card) return;

    await animateSwipe(card, 'like');
    await handleSwipeAction('like');
}

async function superLike() {
    if (!currentUser) {
        showLoginRequired('Login to super like profiles!');
        return;
    }

    const profile = discoveryProfiles[currentProfileIndex];

    // Check if profile exists
    if (!profile) {
        console.error('No profile at index:', currentProfileIndex);
        showStatus('No profile available');
        return;
    }

    try {
        // Use backend API
        if (window.backendAPI && window.backendAPI.isLoggedIn()) {
            const profileId = profile.id || profile.userId;
            if (!profileId) {
                console.error('Profile has no ID:', profile);
                showStatus('Error: Profile has no ID');
                return;
            }
            const result = await window.backendAPI.createInteraction(profileId, 'super_like');

            if (result.is_match) {
                await celebrateMatch(profile, result.match_id);
            } else {
                showStatus(`Super Liked ${profile.name}! 💫`);
            }
        } else if (typeof datingDB !== 'undefined') {
            await datingDB.addInteraction(currentUser.id, profile.id, 'super_like');
            showStatus(`Super Liked ${profile.name}! 💫`);
            await checkAndCelebrateMatch(currentUser.id, profile.id);
        }

        const card = document.getElementById('swipeCard');
        if (card) {
            card.style.transition = 'transform 0.5s ease-out, opacity 0.5s ease-out';
            card.style.transform = 'translateY(-1000px) scale(1.2)';
            card.style.opacity = '0';

            setTimeout(() => {
                card.style.transition = '';
                currentProfileIndex++;
                showCurrentProfile();
            }, 500);
        }
    } catch (error) {
        console.error('Error with super like:', error);
        showStatus('Error processing super like');
    }
}

async function reportCurrentProfile() {
    const profile = discoveryProfiles[currentProfileIndex];

    if (!profile.userId) {
        showStatus('Cannot report sample profiles');
        return;
    }

    const reasons = ['Inappropriate content', 'Harassment', 'Spam', 'Fake profile', 'Other'];

    const modal = document.createElement('div');
    modal.className = 'modal active';

    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h2>Report ${profile.name}</h2>
                <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="form-group">
                    <label>Reason for reporting</label>
                    <select id="reportReason">
                        ${reasons.map(r => `<option value="${r}">${r}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Additional details (optional)</label>
                    <textarea id="reportDetails" rows="3"></textarea>
                </div>
                <div class="form-group">
                    <label class="checkbox-label">
                        <input type="checkbox" id="alsoBlock">
                        Also block this user
                    </label>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Cancel</button>
                <button class="btn btn-danger" onclick="submitReport('${profile.userId}', '${profile.name}')">Submit Report</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

async function submitReport(reportedUserId, reportedName) {
    const reason = document.getElementById('reportReason').value;
    const details = document.getElementById('reportDetails').value;
    const alsoBlock = document.getElementById('alsoBlock').checked;

    try {
        await datingDB.reportUser(currentUser.id, reportedUserId, reason, details);

        if (alsoBlock) {
            await datingDB.blockUser(currentUser.id, reportedUserId, reason);
        }

        showStatus(`Reported ${reportedName}. Thank you for keeping our community safe.`);

        document.querySelector('.modal').remove();

        // Move to next profile
        currentProfileIndex++;
        showCurrentProfile();
    } catch (error) {
        console.error('Error submitting report:', error);
        showStatus('Error submitting report');
    }
}

// Undo last swipe
let lastSwipeAction = null;

async function undoSwipe() {
    if (!lastSwipeAction) {
        showStatus('Nothing to undo');
        return;
    }

    try {
        // Remove last interaction
        const transaction = datingDB.db.transaction(['interactions'], 'readwrite');
        const store = transaction.objectStore('interactions');
        await datingDB.promisifyRequest(store.delete(lastSwipeAction.id));

        // Go back one profile
        currentProfileIndex = Math.max(0, currentProfileIndex - 1);
        showCurrentProfile();

        showStatus('Undo successful!');
        lastSwipeAction = null;
    } catch (error) {
        console.error('Error undoing swipe:', error);
        showStatus('Error undoing swipe');
    }
}

// Celebrate a match
async function celebrateMatch(profile, matchId) {
    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-content match-modal" style="max-width: 400px; text-align: center;">
            <div class="modal-body">
                <div class="match-celebration">
                    <h1 style="font-size: 48px; margin: 20px 0;">🎉</h1>
                    <h2 style="color: var(--primary-color); margin: 10px 0;">It's a Match!</h2>
                    <p style="font-size: 18px; margin: 20px 0;">You and ${profile.name} liked each other</p>
                </div>
            </div>
            <div class="modal-footer" style="justify-content: center; gap: 10px;">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Keep Swiping</button>
                <button class="btn btn-primary" onclick="this.closest('.modal').remove(); showScreen('matches');">View Match</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    // Play celebration sound if available
    if (typeof playSound === 'function') {
        playSound('match');
    }
}
