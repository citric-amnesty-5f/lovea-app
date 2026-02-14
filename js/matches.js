// Match Detection and Management - Backend API Version

// Check for match after liking a profile (backend handles match creation)
async function checkAndCelebrateMatch(interactionResult) {
    try {
        if (interactionResult && interactionResult.is_match) {
            // It's a match! Load match details and show celebration
            const matches = await window.backendAPI.getMatches();
            const match = matches.find(m => m.id === interactionResult.match_id);
            if (match) {
                await showMatchCelebration(match);
            }
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error checking for match:', error);
        return false;
    }
}

// Show "It's a Match!" celebration modal
async function showMatchCelebration(match) {
    try {
        const otherProfile = match.other_user_profile || match.otherProfile;
        const otherName = otherProfile?.name || 'someone';
        const otherAvatar = otherProfile?.photos?.[0]?.url || '👤';
        const userName = currentUser?.profile?.name || currentUser?.name || 'You';

        // Create celebration modal
        const modal = document.createElement('div');
        modal.className = 'match-celebration-modal';
        modal.innerHTML = `
            <div class="match-celebration-content">
                <div class="match-celebration-close" onclick="closeMatchCelebration()">&times;</div>
                <div class="match-celebration-header">
                    <div class="celebration-emoji">🎉</div>
                    <h2>It's a Match!</h2>
                    <p>You and ${otherName} liked each other</p>
                </div>
                <div class="match-profiles">
                    <div class="match-profile-item">
                        <div class="match-profile-avatar">👤</div>
                        <div class="match-profile-name">${userName}</div>
                    </div>
                    <div class="match-heart">❤️</div>
                    <div class="match-profile-item">
                        <div class="match-profile-avatar">${otherAvatar}</div>
                        <div class="match-profile-name">${otherName}</div>
                    </div>
                </div>
                <div class="match-actions">
                    <button class="btn-match-message" onclick="sendFirstMessage(${match.id})">
                        Send Message 💬
                    </button>
                    <button class="btn-match-later" onclick="closeMatchCelebration()">
                        Keep Swiping
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Trigger animation
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);

        // Play celebration animation
        createConfetti();

        // Store reference for later cleanup
        window.currentMatchModal = modal;
    } catch (error) {
        console.error('Error showing match celebration:', error);
    }
}

function closeMatchCelebration() {
    const modal = window.currentMatchModal;
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
            window.currentMatchModal = null;
        }, 300);
    }
}

async function sendFirstMessage(matchId) {
    closeMatchCelebration();

    try {
        // Load matches from backend to get full details
        const matches = await window.backendAPI.getMatches();
        const match = matches.find(m => m.id === matchId);

        if (match) {
            const otherProfile = match.other_user_profile;
            const enhancedMatch = {
                id: match.id,
                otherUser: {
                    id: otherProfile.id,
                    name: otherProfile.name
                },
                otherProfile: {
                    ...otherProfile,
                    aiCompatibility: match.compatibility_score || 0,
                    avatar: otherProfile.photos?.[0]?.url || '👤'
                },
                iceBreakers: match.ai_ice_breakers || [],
                createdAt: match.created_at
            };

            // Switch to messaging screen
            showScreen('messages');
            setTimeout(() => {
                if (typeof openChat === 'function') {
                    openChat(enhancedMatch);
                }
            }, 100);
        }
    } catch (error) {
        console.error('Error opening first message:', error);
    }
}

// Create confetti animation
function createConfetti() {
    const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7', '#a29bfe'];
    const confettiCount = 50;

    for (let i = 0; i < confettiCount; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.left = Math.random() * 100 + '%';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.animationDelay = Math.random() * 3 + 's';
            confetti.style.animationDuration = (Math.random() * 3 + 2) + 's';

            document.body.appendChild(confetti);

            // Remove after animation
            setTimeout(() => {
                confetti.remove();
            }, 5000);
        }, i * 30);
    }
}

// Get all user matches
async function loadUserMatches() {
    try {
        // Check if user is logged in
        if (!currentUser || !window.backendAPI || !window.backendAPI.isLoggedIn()) {
            showLoginRequired('Login to view your matches');
            return;
        }

        // Use backend API to get matches
        const matches = await window.backendAPI.getMatches();

        // Transform matches to expected format
        const matchesWithDetails = matches.map(match => {
            const otherProfile = match.other_user_profile;
            // Add compatibility and avatar to profile
            const profile = {
                ...otherProfile,
                aiCompatibility: match.compatibility_score || otherProfile.ai_compatibility_score || 0,
                avatar: otherProfile.photos?.[0]?.url || '👤'
            };

            return {
                id: match.id,
                matchId: match.id,
                user1_id: match.user1_id,
                user2_id: match.user2_id,
                otherUser: {
                    id: otherProfile.id,
                    name: otherProfile.name,
                    email: otherProfile.email || ''
                },
                otherProfile: profile,
                unreadCount: 0,
                lastMessage: null,
                messageCount: 0,
                createdAt: match.created_at,
                lastMessageAt: match.created_at,
                iceBreakers: match.ai_ice_breakers || [],
                compatibilityScore: match.compatibility_score,
                compatibilityReasons: match.compatibility_reasons || []
            };
        });

        // Sort by most recent activity
        matchesWithDetails.sort((a, b) => {
            const aTime = new Date(a.lastMessageAt || a.createdAt);
            const bTime = new Date(b.lastMessageAt || b.createdAt);
            return bTime - aTime;
        });

        displayMatchesGrid(matchesWithDetails);
    } catch (error) {
        console.error('Error loading matches:', error);
        const container = document.getElementById('matchesGridContainer');
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">❌</div>
                    <h3>Error Loading Matches</h3>
                    <p>${error.message || 'Unknown error'}</p>
                    <button class="btn btn-primary" onclick="loadUserMatches()">Try Again</button>
                </div>
            `;
        }
    }
}

function displayMatchesGrid(matches) {
    const container = document.getElementById('matchesGridContainer');
    if (!container) return;

    container.innerHTML = '';

    if (matches.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">💔</div>
                <h3>No Matches Yet</h3>
                <p>Keep swiping to find your perfect match!</p>
                <button class="btn btn-primary" onclick="showScreen('discover')">Start Swiping</button>
            </div>
        `;
        return;
    }

    const grid = document.createElement('div');
    grid.className = 'matches-grid';

    matches.forEach(match => {
        const card = document.createElement('div');
        card.className = 'match-grid-card';

        const compatibility = Math.round(match.otherProfile?.aiCompatibility || match.compatibilityScore || 0);
        const timeAgo = getTimeAgo(match.createdAt);
        const name = match.otherUser?.name || match.otherProfile?.name || 'Unknown';
        const avatar = match.otherProfile?.avatar || '👤';
        const bio = match.otherProfile?.bio || '';
        const age = match.otherProfile?.age || '';
        const occupation = match.otherProfile?.occupation || '';

        card.innerHTML = `
            <div class="match-grid-avatar">${avatar}</div>
            ${match.unreadCount > 0 ? `<div class="match-grid-badge">${match.unreadCount}</div>` : ''}
            <div class="match-grid-name">${name}${age ? ', ' + age : ''}</div>
            ${occupation ? `<div class="match-grid-occupation">${occupation}</div>` : ''}
            <div class="match-grid-compat">${compatibility}% Match</div>
            <div class="match-grid-time">${timeAgo}</div>
            ${match.messageCount === 0 ? '<div class="match-grid-new">New Match!</div>' : ''}
        `;

        card.onclick = () => {
            showMatchProfile(match);
        };

        grid.appendChild(card);
    });

    container.appendChild(grid);
}

// Show match profile detail view
function showMatchProfile(match) {
    const otherProfile = match.otherProfile;
    const name = match.otherUser?.name || otherProfile?.name || 'Unknown';
    const age = otherProfile?.age || '';
    const bio = otherProfile?.bio || 'No bio yet';
    const occupation = otherProfile?.occupation || '';
    const location = otherProfile?.location || '';
    const compatibility = Math.round(otherProfile?.aiCompatibility || match.compatibilityScore || 0);
    const interests = otherProfile?.interests || [];
    const iceBreakers = match.iceBreakers || [];
    const reasons = match.compatibilityReasons || [];
    const avatar = otherProfile?.avatar || '👤';

    const modal = document.createElement('div');
    modal.className = 'modal active';
    modal.innerHTML = `
        <div class="modal-content" style="max-width: 500px;">
            <div class="modal-header">
                <h2>${name}${age ? ', ' + age : ''}</h2>
                <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div style="text-align: center; margin-bottom: 16px;">
                    <div style="font-size: 64px; margin-bottom: 8px;">${avatar}</div>
                    <div style="font-size: 24px; font-weight: bold; color: #e91e63;">${compatibility}% Match</div>
                </div>

                ${occupation ? `<p style="text-align: center; color: #666; margin-bottom: 4px;">💼 ${occupation}</p>` : ''}
                ${location ? `<p style="text-align: center; color: #666; margin-bottom: 16px;">📍 ${location}</p>` : ''}

                <div style="margin-bottom: 16px;">
                    <h3 style="margin-bottom: 8px;">About</h3>
                    <p style="color: #555;">${bio}</p>
                </div>

                ${interests.length > 0 ? `
                    <div style="margin-bottom: 16px;">
                        <h3 style="margin-bottom: 8px;">Interests</h3>
                        <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                            ${interests.map(i => `<span style="background: #f0f0f0; padding: 4px 12px; border-radius: 16px; font-size: 14px;">${i.icon || ''} ${i.name}</span>`).join('')}
                        </div>
                    </div>
                ` : ''}

                ${reasons.length > 0 ? `
                    <div style="margin-bottom: 16px;">
                        <h3 style="margin-bottom: 8px;">Why You Match</h3>
                        <ul style="color: #555; padding-left: 20px;">
                            ${reasons.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${iceBreakers.length > 0 ? `
                    <div style="margin-bottom: 16px;">
                        <h3 style="margin-bottom: 8px;">Conversation Starters</h3>
                        <div style="display: flex; flex-direction: column; gap: 8px;">
                            ${iceBreakers.map(ib => `
                                <div style="background: #e3f2fd; padding: 10px 14px; border-radius: 12px; cursor: pointer; font-size: 14px;"
                                     onclick="useIceBreaker(${match.id}, '${ib.replace(/'/g, "\\'")}', this)">
                                    💬 ${ib}
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
            <div class="modal-footer" style="display: flex; gap: 8px;">
                <button class="btn btn-secondary" onclick="this.closest('.modal').remove()">Close</button>
                <button class="btn btn-primary" onclick="openChatWithMatch(${match.id}); this.closest('.modal').remove();">
                    Send Message 💬
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

// Use an ice breaker to send as first message
async function useIceBreaker(matchId, message, element) {
    try {
        await window.backendAPI.sendMessage(matchId, message);

        // Visual feedback
        if (element) {
            element.style.background = '#c8e6c9';
            element.innerHTML = '✅ Sent!';
        }

        // Close modal after brief delay and open chat
        setTimeout(() => {
            const modal = element?.closest('.modal');
            if (modal) modal.remove();
            openChatWithMatch(matchId);
        }, 800);
    } catch (error) {
        console.error('Error sending ice breaker:', error);
        if (element) {
            element.style.background = '#ffcdd2';
            element.innerHTML = '❌ Failed to send';
        }
    }
}

// Open chat with a match
async function openChatWithMatch(matchId) {
    try {
        const matches = await window.backendAPI.getMatches();
        const match = matches.find(m => m.id === matchId);

        if (match) {
            const otherProfile = match.other_user_profile;
            const enhancedMatch = {
                id: match.id,
                matchId: match.id,
                otherUser: {
                    id: otherProfile.id,
                    name: otherProfile.name
                },
                otherProfile: {
                    ...otherProfile,
                    aiCompatibility: match.compatibility_score || 0,
                    avatar: otherProfile.photos?.[0]?.url || '👤'
                },
                iceBreakers: match.ai_ice_breakers || [],
                createdAt: match.created_at
            };

            showScreen('messages');
            setTimeout(() => {
                if (typeof openChat === 'function') {
                    openChat(enhancedMatch);
                }
            }, 100);
        }
    } catch (error) {
        console.error('Error opening chat:', error);
    }
}

function getTimeAgo(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return time.toLocaleDateString();
}

// Update match count badge in navigation
async function updateMatchBadge() {
    try {
        if (!currentUser || !window.backendAPI || !window.backendAPI.isLoggedIn()) {
            return;
        }

        const matches = await window.backendAPI.getMatches();
        const badge = document.getElementById('matchesBadge');
        if (badge) {
            if (matches.length > 0) {
                badge.textContent = matches.length > 9 ? '9+' : matches.length;
                badge.style.display = 'block';
            } else {
                badge.style.display = 'none';
            }
        }
    } catch (error) {
        console.error('Error updating match badge:', error);
    }
}
