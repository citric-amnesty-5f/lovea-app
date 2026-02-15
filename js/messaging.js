// Messaging System Functions

let currentChatMatch = null;
let messagePollingInterval = null;

// Show messaging interface
async function showMessagingScreen() {
    try {
        // Check if user is logged in
        if (!currentUser || !window.backendAPI || !window.backendAPI.isLoggedIn()) {
            showLoginRequired('Login to view messages');
            return;
        }

        // Use backend API to get matches
        const matches = await window.backendAPI.getMatches();

        if (matches.length === 0) {
            const container = document.getElementById('matchesContainer');
            if (container) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">💬</div>
                        <h3>No Matches Yet</h3>
                        <p>Start liking profiles to make connections!</p>
                        <button class="btn btn-primary" onclick="showScreen('discover')">Start Swiping</button>
                    </div>
                `;
            }
            return;
        }

        // Transform matches to expected format
        const matchesWithProfiles = matches.map(match => {
            // Add compatibility and other fields to profile
            const profile = {
                ...match.other_user_profile,
                aiCompatibility: match.compatibility_score || match.other_user_profile.ai_compatibility_score || 0,
                avatar: match.other_user_profile.photos?.[0]?.url || '👤'
            };

            return {
                id: match.id,
                otherUser: {
                    id: match.other_user_profile.id,
                    name: match.other_user_profile.name,
                    email: match.other_user_profile.email || ''
                },
                otherProfile: profile,
                unreadCount: 0,  // Backend doesn't provide this yet
                messageCount: 0  // Backend doesn't provide this yet
            };
        });

        displayMatchesList(matchesWithProfiles);
    } catch (error) {
        console.error('Error loading matches:', error);
        const container = document.getElementById('matchesContainer');
        if (container) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">❌</div>
                    <h3>Error Loading Matches</h3>
                    <p>${error.message || 'Unknown error'}</p>
                    <button class="btn btn-primary" onclick="showMessagingScreen()">Try Again</button>
                </div>
            `;
        }
    }
}

function displayMatchesList(matches) {
    const container = document.getElementById('matchesContainer');
    if (!container) return;

    container.innerHTML = '<h3>Your Matches</h3>';

    if (matches.length === 0) {
        container.innerHTML += '<p class="empty-state">No matches yet. Keep swiping!</p>';
        return;
    }

    const matchesList = document.createElement('div');
    matchesList.className = 'matches-list';

    matches.forEach(match => {
        const matchCard = document.createElement('div');
        matchCard.className = 'match-card';
        if (match.unreadCount > 0) {
            matchCard.classList.add('has-unread');
        }

        const msgAvatarRaw = match.otherProfile?.avatar || '👤';
        const msgApiBase = window.backendAPI ? window.backendAPI.apiBaseUrl : '';
        const msgAvatarHtml = (msgAvatarRaw.startsWith('/') || msgAvatarRaw.startsWith('http'))
            ? `<img src="${msgApiBase}${msgAvatarRaw}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;" alt="">`
            : msgAvatarRaw;

        matchCard.innerHTML = `
            <div class="match-avatar">${msgAvatarHtml}</div>
            <div class="match-info">
                <div class="match-name">${match.otherUser?.name || 'Unknown'}</div>
                <div class="match-preview">${match.lastMessageAt ? 'Tap to chat' : 'Say hi!'}</div>
            </div>
            ${match.unreadCount > 0 ? `<div class="unread-badge">${match.unreadCount}</div>` : ''}
            <div class="match-arrow">›</div>
        `;

        matchCard.onclick = () => openChat(match);
        matchesList.appendChild(matchCard);
    });

    container.appendChild(matchesList);
}

async function openChat(match) {
    currentChatMatch = match;

    // Show chat interface
    const chatScreen = document.getElementById('chatScreen');
    const matchesScreen = document.getElementById('matchesScreen');

    if (matchesScreen) matchesScreen.style.display = 'none';
    if (chatScreen) chatScreen.style.display = 'block';

    // Set chat header
    document.getElementById('chatPartnerName').textContent = match.otherUser?.name || 'Unknown';
    const chatAvatarRaw = match.otherProfile?.avatar || '👤';
    const chatAvatarEl = document.getElementById('chatPartnerAvatar');
    const chatApiBase = window.backendAPI ? window.backendAPI.apiBaseUrl : '';
    if (chatAvatarRaw.startsWith('/') || chatAvatarRaw.startsWith('http')) {
        chatAvatarEl.innerHTML = `<img src="${chatApiBase}${chatAvatarRaw}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;" alt="">`;
    } else {
        chatAvatarEl.textContent = chatAvatarRaw;
    }

    // Load messages
    await loadChatMessages(match.id);

    // Mark messages as read (using backend API)
    try {
        await window.backendAPI.markConversationRead(match.id);
    } catch (error) {
        console.log('Could not mark as read:', error);
    }

    // Start polling for new messages
    startMessagePolling(match.id);

    // Load conversation starters if no messages
    try {
        const conversation = await window.backendAPI.getConversation(match.id);
        const messages = conversation.messages || [];
        if (messages.length === 0) {
            showConversationStarters(match);
        }
    } catch (error) {
        console.log('Could not load conversation starters:', error);
        showConversationStarters(match);
    }
}

async function loadChatMessages(matchId) {
    try {
        // Use backend API
        const conversation = await window.backendAPI.getConversation(matchId);
        const messages = conversation.messages || [];

        const messagesContainer = document.getElementById('messagesContainer');

        if (!messagesContainer) return;

        messagesContainer.innerHTML = '';

        messages.forEach(message => {
            const messageEl = createMessageElement(message);
            messagesContainer.appendChild(messageEl);
        });

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } catch (error) {
        console.error('Error loading messages:', error);
        // Show empty state or error message
        const messagesContainer = document.getElementById('messagesContainer');
        if (messagesContainer) {
            messagesContainer.innerHTML = '<div class="empty-state">No messages yet. Start the conversation!</div>';
        }
    }
}

function createMessageElement(message) {
    const messageDiv = document.createElement('div');
    // Backend uses sender_id, old code used senderId
    const senderId = message.sender_id || message.senderId;
    messageDiv.className = senderId === currentUser.id ? 'message message-sent' : 'message message-received';

    // Backend uses created_at, old code used timestamp
    const timestamp = message.created_at || message.timestamp;
    const time = new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    messageDiv.innerHTML = `
        <div class="message-content">${escapeHtml(message.content)}</div>
        <div class="message-time">${time}</div>
    `;

    return messageDiv;
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const content = input.value.trim();

    if (!content || !currentChatMatch) return;

    try {
        // Disable input while sending
        input.disabled = true;

        // Use backend API to send message
        await window.backendAPI.sendMessage(currentChatMatch.id, content);

        // Clear input
        input.value = '';

        // Reload messages
        await loadChatMessages(currentChatMatch.id);

        // Update match list
        currentChatMatch.lastMessageAt = new Date().toISOString();
    } catch (error) {
        console.error('Error sending message:', error);
        showStatus('Failed to send message: ' + (error.message || 'Unknown error'));
    } finally {
        input.disabled = false;
        input.focus();
    }
}

function startMessagePolling(matchId) {
    // Clear any existing interval
    if (messagePollingInterval) {
        clearInterval(messagePollingInterval);
    }

    // Poll every 2 seconds for new messages
    messagePollingInterval = setInterval(async () => {
        if (currentChatMatch && currentChatMatch.id === matchId) {
            try {
                const conversation = await window.backendAPI.getConversation(matchId);
                const messages = conversation.messages || [];
                const container = document.getElementById('messagesContainer');

                if (container && container.children.length !== messages.length) {
                    await loadChatMessages(matchId);
                    await window.backendAPI.markConversationRead(matchId);
                }
            } catch (error) {
                console.error('Error polling messages:', error);
            }
        }
    }, 2000);
}

function stopMessagePolling() {
    if (messagePollingInterval) {
        clearInterval(messagePollingInterval);
        messagePollingInterval = null;
    }
}

function closeChat() {
    stopMessagePolling();
    currentChatMatch = null;

    const chatScreen = document.getElementById('chatScreen');
    const matchesScreen = document.getElementById('matchesScreen');

    if (chatScreen) chatScreen.style.display = 'none';
    if (matchesScreen) {
        matchesScreen.style.display = 'block';
        showMessagingScreen(); // Refresh matches list
    }
}

async function showConversationStarters(match) {
    if (!aiEngine.hasApiKey()) return;

    try {
        const userProfile = await datingDB.getUserProfile(currentUser.id);
        if (!userProfile) return;

        const starters = await aiEngine.generateConversationStarters(userProfile, match.otherProfile);

        const startersContainer = document.createElement('div');
        startersContainer.className = 'conversation-starters';
        startersContainer.innerHTML = '<div class="starters-header">Conversation Starters:</div>';

        starters.forEach(starter => {
            const starterBtn = document.createElement('button');
            starterBtn.className = 'starter-btn';
            starterBtn.textContent = starter;
            starterBtn.onclick = () => {
                document.getElementById('messageInput').value = starter;
                startersContainer.remove();
            };
            startersContainer.appendChild(starterBtn);
        });

        document.getElementById('messagesContainer').appendChild(startersContainer);
    } catch (error) {
        console.error('Error showing conversation starters:', error);
    }
}

// Handle Enter key in message input
function setupMessageInput() {
    const input = document.getElementById('messageInput');
    if (input) {
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
