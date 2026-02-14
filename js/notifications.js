// Notification System

let notificationCheckInterval = null;

// Start checking for notifications
function startNotificationPolling() {
    if (!currentUser) return;

    // Check immediately
    checkNotifications();

    // Then check every 10 seconds
    if (notificationCheckInterval) {
        clearInterval(notificationCheckInterval);
    }

    notificationCheckInterval = setInterval(checkNotifications, 10000);
}

function stopNotificationPolling() {
    if (notificationCheckInterval) {
        clearInterval(notificationCheckInterval);
        notificationCheckInterval = null;
    }
}

async function checkNotifications() {
    if (!currentUser) return;

    try {
        const unreadNotifications = await datingDB.getUserNotifications(currentUser.id, true);

        // Update notification badge
        updateNotificationBadge(unreadNotifications.length);

        // Update match badge
        await updateMatchBadge();

    } catch (error) {
        console.error('Error checking notifications:', error);
    }
}

function updateNotificationBadge(count) {
    const badge = document.getElementById('notificationsBadge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count > 9 ? '9+' : count;
            badge.style.display = 'block';
        } else {
            badge.style.display = 'none';
        }
    }
}

async function showNotifications() {
    try {
        // Check if user is logged in
        if (!currentUser) {
            showLoginRequired('Login to view notifications');
            return;
        }

        let notifications = [];

        // Use backend API (when endpoint is available)
        // For now, show a placeholder
        if (window.backendAPI && window.backendAPI.isLoggedIn()) {
            // Backend doesn't have notifications endpoint yet
            // Show empty state
            notifications = [];
        } else if (typeof datingDB !== 'undefined') {
            // Fallback to local database
            notifications = await datingDB.getUserNotifications(currentUser.id);
        }

        displayNotificationsList(notifications);
    } catch (error) {
        console.error('Error loading notifications:', error);
        showStatus('Error loading notifications');
    }
}

function displayNotificationsList(notifications) {
    const container = document.getElementById('notificationsContainer');
    if (!container) return;

    container.innerHTML = '<h3>Notifications</h3>';

    if (notifications.length === 0) {
        container.innerHTML += '<p class="empty-state">No notifications yet</p>';
        return;
    }

    const list = document.createElement('div');
    list.className = 'notifications-list';

    notifications.forEach(notification => {
        const item = document.createElement('div');
        item.className = `notification-item ${!notification.read ? 'unread' : ''}`;

        const icon = getNotificationIcon(notification.type);
        const time = getTimeAgo(notification.timestamp);

        item.innerHTML = `
            <div class="notification-icon">${icon}</div>
            <div class="notification-content">
                <div class="notification-message">${notification.message}</div>
                <div class="notification-time">${time}</div>
            </div>
            ${!notification.read ? '<div class="notification-dot"></div>' : ''}
        `;

        item.onclick = () => handleNotificationClick(notification);

        list.appendChild(item);
    });

    const clearBtn = document.createElement('button');
    clearBtn.className = 'btn btn-secondary';
    clearBtn.textContent = 'Mark All as Read';
    clearBtn.onclick = markAllNotificationsRead;

    container.appendChild(list);
    container.appendChild(clearBtn);
}

function getNotificationIcon(type) {
    const icons = {
        'match': '❤️',
        'message': '💬',
        'like': '👍',
        'super_like': '⭐'
    };
    return icons[type] || '🔔';
}

async function handleNotificationClick(notification) {
    try {
        // Mark as read
        await datingDB.markNotificationAsRead(notification.id);

        // Handle notification action
        if (notification.type === 'match' && notification.data?.matchId) {
            // Navigate to matches/messages
            const match = await datingDB.promisifyRequest(
                datingDB.db.transaction(['matches'], 'readonly')
                    .objectStore('matches')
                    .get(notification.data.matchId)
            );

            if (match) {
                const otherUserId = match.user1Id === currentUser.id ? match.user2Id : match.user1Id;
                const otherUser = await datingDB.promisifyRequest(
                    datingDB.db.transaction(['users'], 'readonly').objectStore('users').get(otherUserId)
                );
                const otherProfile = await datingDB.getUserProfile(otherUserId);

                const enhancedMatch = { ...match, otherUser, otherProfile };

                showScreen('messages');
                setTimeout(() => openChat(enhancedMatch), 100);
            }
        } else if (notification.type === 'message' && notification.data?.matchId) {
            // Navigate to specific chat
            const match = await datingDB.promisifyRequest(
                datingDB.db.transaction(['matches'], 'readonly')
                    .objectStore('matches')
                    .get(notification.data.matchId)
            );

            if (match) {
                const otherUserId = match.user1Id === currentUser.id ? match.user2Id : match.user1Id;
                const otherUser = await datingDB.promisifyRequest(
                    datingDB.db.transaction(['users'], 'readonly').objectStore('users').get(otherUserId)
                );
                const otherProfile = await datingDB.getUserProfile(otherUserId);

                const enhancedMatch = { ...match, otherUser, otherProfile };

                showScreen('messages');
                setTimeout(() => openChat(enhancedMatch), 100);
            }
        }

        // Refresh notifications
        await checkNotifications();
        await showNotifications();
    } catch (error) {
        console.error('Error handling notification click:', error);
    }
}

async function markAllNotificationsRead() {
    try {
        await datingDB.markAllNotificationsAsRead(currentUser.id);
        showStatus('All notifications marked as read');
        await checkNotifications();
        await showNotifications();
    } catch (error) {
        console.error('Error marking notifications as read:', error);
        showStatus('Error updating notifications');
    }
}

// Show notification toast
function showNotificationToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `notification-toast notification-${type}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
