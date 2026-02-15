/**
 * Backend API Integration
 * Replaces IndexedDB with FastAPI backend calls
 */

const DEFAULT_API_PORT = '8000';

function resolveApiBaseUrl() {
    const queryOverride = new URLSearchParams(window.location.search).get('api');
    const storageOverride = localStorage.getItem('loveai_api_base_url');
    const globalOverride = window.LOVEAI_API_BASE_URL;
    const override = globalOverride || storageOverride || queryOverride;

    if (override) {
        return override.replace(/\/+$/, '');
    }

    const { protocol, hostname } = window.location;
    if (!hostname) {
        return `http://localhost:${DEFAULT_API_PORT}`;
    }

    const isPrivateNetwork =
        /^10\./.test(hostname) ||
        /^192\.168\./.test(hostname) ||
        /^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname);
    const isLocalHost = hostname === 'localhost' || hostname === '127.0.0.1' || hostname.endsWith('.local');
    if (isLocalHost || isPrivateNetwork) {
        return `http://${hostname}:${DEFAULT_API_PORT}`;
    }

    // For public hosts, default to same origin (useful when frontend+API share one domain).
    return window.location.origin;
}

class BackendAPI {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.currentUserId = localStorage.getItem('user_id');
        this.apiBaseUrl = resolveApiBaseUrl();
    }

    // Helper method to get auth headers
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        return headers;
    }

    // Helper method for API calls
    async apiCall(endpoint, method = 'GET', data = null) {
        const options = {
            method,
            headers: this.getHeaders()
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}${endpoint}`, options);

            if (!response.ok) {
                let errorMessage = `Request failed with status ${response.status}`;
                let errorDetail = null;

                try {
                    const error = await response.json();
                    errorDetail = error; // Store full error for logging

                    // Handle Pydantic validation errors (array format)
                    if (Array.isArray(error.detail)) {
                        const firstError = error.detail[0];
                        errorMessage = firstError.msg || firstError.message || 'Validation error';
                    }
                    // Handle simple error detail (string format)
                    else if (error.detail) {
                        errorMessage = error.detail;
                    }
                } catch (parseError) {
                    // If response isn't JSON, use status text
                    errorMessage = response.statusText || errorMessage;
                }

                // Log full error details for debugging
                console.error('[BackendAPI] Error Response:', {
                    status: response.status,
                    endpoint: endpoint,
                    method: method,
                    errorDetail: errorDetail,
                    errorMessage: errorMessage
                });

                // Add helpful context for common errors
                if (response.status === 401) {
                    const isAuthEndpoint = endpoint === '/auth/login' || endpoint === '/auth/register';
                    if (!isAuthEndpoint) {
                        errorMessage = 'Session expired. Please login again.';
                        // Clear invalid token for authenticated endpoints
                        localStorage.removeItem('auth_token');
                        localStorage.removeItem('user_id');
                    }
                } else if (response.status === 403) {
                    errorMessage = 'Access denied. ' + errorMessage;
                } else if (response.status === 404) {
                    errorMessage = 'Resource not found. ' + errorMessage;
                } else if (response.status >= 500) {
                    errorMessage = 'Server error. Please try again later. Details: ' + errorMessage;
                }

                throw new Error(errorMessage);
            }

            return await response.json();
        } catch (error) {
            // Network errors
            if (error.name === 'TypeError') {
                throw new Error('Network error. Please check your connection and API URL.');
            }

            console.error(`API Error (${method} ${endpoint}):`, error);
            throw error;
        }
    }

    // ========================================================================
    // Authentication
    // ========================================================================

    async register(userData) {
        try {
            const payload = { ...userData };
            if (typeof payload.email === 'string') {
                payload.email = payload.email.trim().toLowerCase();
            }
            const result = await this.apiCall('/auth/register', 'POST', payload);

            // Store token and user ID
            this.token = result.access_token;
            this.currentUserId = result.user_id;
            localStorage.setItem('auth_token', this.token);
            localStorage.setItem('user_id', this.currentUserId);

            return result;
        } catch (error) {
            console.error('Registration error:', error);
            throw error;
        }
    }

    async login(email, password) {
        try {
            const normalizedEmail = typeof email === 'string' ? email.trim().toLowerCase() : email;
            const result = await this.apiCall('/auth/login', 'POST', { email: normalizedEmail, password });

            // Store token and user ID
            this.token = result.access_token;
            this.currentUserId = result.user_id;
            localStorage.setItem('auth_token', this.token);
            localStorage.setItem('user_id', this.currentUserId);

            return result;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    async logout() {
        try {
            await this.apiCall('/auth/logout', 'POST');
        } finally {
            // Clear local storage
            this.token = null;
            this.currentUserId = null;
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user_id');
        }
    }

    isLoggedIn() {
        return !!this.token && !!this.currentUserId;
    }

    getCurrentUserId() {
        return this.currentUserId;
    }

    // ========================================================================
    // Profile Management
    // ========================================================================

    async getMyProfile() {
        return await this.apiCall('/profiles/me');
    }

    async getProfile(userId) {
        return await this.apiCall(`/profiles/${userId}`);
    }

    async updateProfile(profileData) {
        return await this.apiCall('/profiles/me', 'PUT', profileData);
    }

    async completeOnboarding() {
        return await this.apiCall('/profiles/complete-onboarding', 'POST');
    }

    // ========================================================================
    // Interests
    // ========================================================================

    async getAllInterests() {
        return await this.apiCall('/profiles/interests/all');
    }

    async addInterests(interestIds) {
        return await this.apiCall('/profiles/me/interests', 'POST', interestIds);
    }

    async removeInterest(interestId) {
        return await this.apiCall(`/profiles/me/interests/${interestId}`, 'DELETE');
    }

    // ========================================================================
    // Photos
    // ========================================================================

    async addPhoto(photoData) {
        return await this.apiCall('/profiles/me/photos', 'POST', photoData);
    }

    async uploadPhoto(base64Data, isPrimary = false, order = 0) {
        return await this.apiCall('/profiles/me/photos/upload', 'POST', {
            data: base64Data,
            is_primary: isPrimary,
            order: order
        });
    }

    async deletePhoto(photoId) {
        return await this.apiCall(`/profiles/me/photos/${photoId}`, 'DELETE');
    }

    // ========================================================================
    // Preferences
    // ========================================================================

    async getPreferences() {
        return await this.apiCall('/profiles/me/preferences');
    }

    async updatePreferences(preferencesData) {
        return await this.apiCall('/profiles/me/preferences', 'PUT', preferencesData);
    }

    // ========================================================================
    // Discovery & Matching
    // ========================================================================

    async getDiscoveryProfiles(limit = 10) {
        return await this.apiCall(`/discovery/profiles?limit=${limit}`);
    }

    async createInteraction(toUserId, interactionType) {
        return await this.apiCall('/discovery/interact', 'POST', {
            to_user_id: toUserId,
            interaction_type: interactionType
        });
    }

    async getMatches() {
        return await this.apiCall('/discovery/matches');
    }

    async unmatch(matchId) {
        return await this.apiCall(`/discovery/matches/${matchId}`, 'DELETE');
    }

    // ========================================================================
    // Messaging
    // ========================================================================

    async sendMessage(matchId, content) {
        return await this.apiCall('/messages/', 'POST', {
            match_id: matchId,
            content
        });
    }

    async getConversations() {
        return await this.apiCall('/messages/conversations');
    }

    async getConversation(matchId) {
        return await this.apiCall(`/messages/conversations/${matchId}`);
    }

    async markConversationRead(matchId) {
        return await this.apiCall(`/messages/conversations/${matchId}/read`, 'PUT');
    }

    // ========================================================================
    // WebSocket for Real-time Chat
    // ========================================================================

    connectWebSocket() {
        if (!this.token) {
            throw new Error('Not authenticated');
        }

        const wsProtocol = this.apiBaseUrl.startsWith('https') ? 'wss' : 'ws';
        const wsHost = this.apiBaseUrl.replace(/^https?:\/\//, '');
        const wsUrl = `${wsProtocol}://${wsHost}/messages/ws?token=${this.token}`;
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log('WebSocket connected');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleWebSocketMessage(data);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            // Attempt to reconnect after 5 seconds
            setTimeout(() => {
                if (this.isLoggedIn()) {
                    this.connectWebSocket();
                }
            }, 5000);
        };

        return this.ws;
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'new_message':
                // Trigger custom event for new message
                window.dispatchEvent(new CustomEvent('newMessage', { detail: data.message }));
                break;
            case 'typing':
                // Trigger custom event for typing indicator
                window.dispatchEvent(new CustomEvent('typing', { detail: data }));
                break;
            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    sendWebSocketMessage(type, data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, ...data }));
        }
    }

    disconnectWebSocket() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Create global API instance
window.backendAPI = new BackendAPI();

// Shared utility: convert a File to a base64 data URI
function fileToBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BackendAPI;
}
