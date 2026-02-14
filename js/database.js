// IndexedDB Database for Dating App
class DatingAppDB {
    constructor() {
        this.dbName = 'LoveAIDB';
        this.version = 1;
        this.db = null;
    }

    async init() {
        return new Promise((resolve, reject) => {
            // Check if IndexedDB is available
            if (!window.indexedDB) {
                reject(new Error('IndexedDB is not supported in this browser'));
                return;
            }

            const request = indexedDB.open(this.dbName, this.version);

            request.onerror = (event) => {
                console.error('Database failed to open:', event.target.error);
                const errorMsg = event.target.error ? event.target.error.message : 'Unknown error';
                reject(new Error('Failed to open database: ' + errorMsg));
            };

            request.onblocked = () => {
                console.warn('Database opening blocked - please close other tabs');
                reject(new Error('Database blocked - close other tabs and try again'));
            };

            request.onsuccess = () => {
                this.db = request.result;
                console.log('Database opened successfully');

                // Handle connection errors
                this.db.onerror = (event) => {
                    console.error('Database error:', event.target.error);
                };

                resolve(this.db);
            };

            request.onupgradeneeded = (e) => {
                this.db = e.target.result;

                // Users store
                if (!this.db.objectStoreNames.contains('users')) {
                    const userStore = this.db.createObjectStore('users', { keyPath: 'id', autoIncrement: true });
                    userStore.createIndex('email', 'email', { unique: true });
                    userStore.createIndex('isAdmin', 'isAdmin', { unique: false });
                }

                // Profiles store
                if (!this.db.objectStoreNames.contains('profiles')) {
                    const profileStore = this.db.createObjectStore('profiles', { keyPath: 'id', autoIncrement: true });
                    profileStore.createIndex('userId', 'userId', { unique: false });
                    profileStore.createIndex('gender', 'gender', { unique: false });
                    profileStore.createIndex('ageRange', 'ageRange', { unique: false });
                }

                // Matches store
                if (!this.db.objectStoreNames.contains('matches')) {
                    const matchStore = this.db.createObjectStore('matches', { keyPath: 'id', autoIncrement: true });
                    matchStore.createIndex('user1Id', 'user1Id', { unique: false });
                    matchStore.createIndex('user2Id', 'user2Id', { unique: false });
                    matchStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                // Messages store
                if (!this.db.objectStoreNames.contains('messages')) {
                    const messageStore = this.db.createObjectStore('messages', { keyPath: 'id', autoIncrement: true });
                    messageStore.createIndex('matchId', 'matchId', { unique: false });
                    messageStore.createIndex('senderId', 'senderId', { unique: false });
                    messageStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                // Likes store
                if (!this.db.objectStoreNames.contains('likes')) {
                    const likeStore = this.db.createObjectStore('likes', { keyPath: 'id', autoIncrement: true });
                    likeStore.createIndex('fromUserId', 'fromUserId', { unique: false });
                    likeStore.createIndex('toUserId', 'toUserId', { unique: false });
                }

                // Notifications store
                if (!this.db.objectStoreNames.contains('notifications')) {
                    const notifStore = this.db.createObjectStore('notifications', { keyPath: 'id', autoIncrement: true });
                    notifStore.createIndex('userId', 'userId', { unique: false });
                    notifStore.createIndex('timestamp', 'timestamp', { unique: false });
                }

                console.log('Database setup complete');
            };
        });
    }

    // User operations
    async createUser(userData) {
        const transaction = this.db.transaction(['users'], 'readwrite');
        const store = transaction.objectStore('users');

        // Check if email already exists
        const emailIndex = store.index('email');
        const existingUser = await new Promise((resolve, reject) => {
            const request = emailIndex.get(userData.email);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });

        if (existingUser) {
            throw new Error('Email already registered');
        }

        const user = {
            name: userData.name,
            email: userData.email,
            password: userData.password,
            age: parseInt(userData.age),
            gender: userData.gender,
            isAdmin: userData.isAdmin || false,
            createdAt: new Date().toISOString()
        };

        return new Promise((resolve, reject) => {
            const request = store.add(user);
            request.onsuccess = () => {
                user.id = request.result;
                resolve(user);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async verifyUser(email, password) {
        const transaction = this.db.transaction(['users'], 'readonly');
        const store = transaction.objectStore('users');
        const index = store.index('email');

        return new Promise((resolve, reject) => {
            const request = index.get(email);
            request.onsuccess = () => {
                const user = request.result;
                if (!user) {
                    reject(new Error('User not found'));
                } else if (user.password !== password) {
                    reject(new Error('Invalid password'));
                } else {
                    resolve(user);
                }
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getUserById(userId) {
        const transaction = this.db.transaction(['users'], 'readonly');
        const store = transaction.objectStore('users');

        return new Promise((resolve, reject) => {
            const request = store.get(userId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getAllUsers() {
        const transaction = this.db.transaction(['users'], 'readonly');
        const store = transaction.objectStore('users');

        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // Profile operations
    async createProfile(profileData) {
        const transaction = this.db.transaction(['profiles'], 'readwrite');
        const store = transaction.objectStore('profiles');

        return new Promise((resolve, reject) => {
            const request = store.add(profileData);
            request.onsuccess = () => {
                profileData.id = request.result;
                resolve(profileData);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getUserProfile(userId) {
        const transaction = this.db.transaction(['profiles'], 'readonly');
        const store = transaction.objectStore('profiles');
        const index = store.index('userId');

        return new Promise((resolve, reject) => {
            const request = index.get(userId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async updateProfile(userId, updates) {
        const profile = await this.getUserProfile(userId);
        if (!profile) {
            throw new Error('Profile not found');
        }

        const updatedProfile = { ...profile, ...updates };
        const transaction = this.db.transaction(['profiles'], 'readwrite');
        const store = transaction.objectStore('profiles');

        return new Promise((resolve, reject) => {
            const request = store.put(updatedProfile);
            request.onsuccess = () => resolve(updatedProfile);
            request.onerror = () => reject(request.error);
        });
    }

    async getAllProfiles() {
        const transaction = this.db.transaction(['profiles'], 'readonly');
        const store = transaction.objectStore('profiles');

        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // Match operations
    async createMatch(user1Id, user2Id) {
        const match = {
            user1Id,
            user2Id,
            timestamp: new Date().toISOString(),
            lastMessage: null
        };

        const transaction = this.db.transaction(['matches'], 'readwrite');
        const store = transaction.objectStore('matches');

        return new Promise((resolve, reject) => {
            const request = store.add(match);
            request.onsuccess = () => {
                match.id = request.result;
                resolve(match);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getUserMatches(userId) {
        const transaction = this.db.transaction(['matches'], 'readonly');
        const store = transaction.objectStore('matches');

        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => {
                const matches = request.result.filter(m =>
                    m.user1Id === userId || m.user2Id === userId
                );
                resolve(matches);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getMatchById(matchId) {
        const transaction = this.db.transaction(['matches'], 'readonly');
        const store = transaction.objectStore('matches');

        return new Promise((resolve, reject) => {
            const request = store.get(matchId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async updateMatch(matchId, updates) {
        const match = await this.getMatchById(matchId);
        if (!match) {
            throw new Error('Match not found');
        }

        const updatedMatch = { ...match, ...updates };
        const transaction = this.db.transaction(['matches'], 'readwrite');
        const store = transaction.objectStore('matches');

        return new Promise((resolve, reject) => {
            const request = store.put(updatedMatch);
            request.onsuccess = () => resolve(updatedMatch);
            request.onerror = () => reject(request.error);
        });
    }

    // Like operations
    async createLike(fromUserId, toUserId, type = 'like') {
        const like = {
            fromUserId,
            toUserId,
            type, // 'like', 'superlike', 'pass'
            timestamp: new Date().toISOString()
        };

        const transaction = this.db.transaction(['likes'], 'readwrite');
        const store = transaction.objectStore('likes');

        return new Promise((resolve, reject) => {
            const request = store.add(like);
            request.onsuccess = () => {
                like.id = request.result;
                resolve(like);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async checkMutualLike(user1Id, user2Id) {
        const transaction = this.db.transaction(['likes'], 'readonly');
        const store = transaction.objectStore('likes');

        return new Promise((resolve, reject) => {
            const request = store.getAll();
            request.onsuccess = () => {
                const likes = request.result;
                const like1 = likes.find(l => l.fromUserId === user1Id && l.toUserId === user2Id && l.type === 'like');
                const like2 = likes.find(l => l.fromUserId === user2Id && l.toUserId === user1Id && l.type === 'like');
                resolve(like1 && like2);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getUserLikes(userId) {
        const transaction = this.db.transaction(['likes'], 'readonly');
        const store = transaction.objectStore('likes');
        const index = store.index('fromUserId');

        return new Promise((resolve, reject) => {
            const request = index.getAll(userId);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    // Message operations
    async createMessage(matchId, senderId, text) {
        const message = {
            matchId,
            senderId,
            text,
            timestamp: new Date().toISOString(),
            read: false
        };

        const transaction = this.db.transaction(['messages'], 'readwrite');
        const store = transaction.objectStore('messages');

        return new Promise((resolve, reject) => {
            const request = store.add(message);
            request.onsuccess = () => {
                message.id = request.result;
                resolve(message);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getMatchMessages(matchId) {
        const transaction = this.db.transaction(['messages'], 'readonly');
        const store = transaction.objectStore('messages');
        const index = store.index('matchId');

        return new Promise((resolve, reject) => {
            const request = index.getAll(matchId);
            request.onsuccess = () => {
                const messages = request.result;
                messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
                resolve(messages);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async markMessagesAsRead(matchId, userId) {
        const messages = await this.getMatchMessages(matchId);
        const transaction = this.db.transaction(['messages'], 'readwrite');
        const store = transaction.objectStore('messages');

        const unreadMessages = messages.filter(m => m.senderId !== userId && !m.read);

        return Promise.all(unreadMessages.map(message => {
            message.read = true;
            return new Promise((resolve, reject) => {
                const request = store.put(message);
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            });
        }));
    }

    // Notification operations
    async createNotification(userId, type, message, data = {}) {
        const notification = {
            userId,
            type,
            message,
            data,
            timestamp: new Date().toISOString(),
            read: false
        };

        const transaction = this.db.transaction(['notifications'], 'readwrite');
        const store = transaction.objectStore('notifications');

        return new Promise((resolve, reject) => {
            const request = store.add(notification);
            request.onsuccess = () => {
                notification.id = request.result;
                resolve(notification);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async getUserNotifications(userId) {
        const transaction = this.db.transaction(['notifications'], 'readonly');
        const store = transaction.objectStore('notifications');
        const index = store.index('userId');

        return new Promise((resolve, reject) => {
            const request = index.getAll(userId);
            request.onsuccess = () => {
                const notifications = request.result;
                notifications.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
                resolve(notifications);
            };
            request.onerror = () => reject(request.error);
        });
    }

    async markNotificationAsRead(notificationId) {
        const transaction = this.db.transaction(['notifications'], 'readwrite');
        const store = transaction.objectStore('notifications');

        return new Promise((resolve, reject) => {
            const getRequest = store.get(notificationId);
            getRequest.onsuccess = () => {
                const notification = getRequest.result;
                if (notification) {
                    notification.read = true;
                    const putRequest = store.put(notification);
                    putRequest.onsuccess = () => resolve(notification);
                    putRequest.onerror = () => reject(putRequest.error);
                } else {
                    reject(new Error('Notification not found'));
                }
            };
            getRequest.onerror = () => reject(getRequest.error);
        });
    }

    // Initialize default data
    async initializeDefaultData() {
        try {
            const users = await this.getAllUsers();
            if (users.length > 0) {
                console.log('Default data already exists');
                return;
            }

            console.log('Creating default admin user...');
            await this.createUser({
                name: 'Admin',
                email: 'admin@loveai.com',
                password: 'admin123',
                age: 30,
                gender: 'other',
                isAdmin: true
            });

            // Create sample profiles for browsing
            console.log('Creating sample profiles...');
            const sampleProfiles = [
                {
                    name: 'Emma',
                    age: 28,
                    gender: 'female',
                    bio: 'Love hiking, coffee, and good conversations. Looking for someone who enjoys the outdoors as much as I do!',
                    location: 'San Francisco, CA',
                    occupation: 'Software Engineer',
                    interests: ['Hiking', 'Coffee', 'Reading', 'Travel', 'Photography'],
                    avatar: '👩',
                    photos: []
                },
                {
                    name: 'James',
                    age: 32,
                    gender: 'male',
                    bio: 'Fitness enthusiast and foodie. Always up for trying new restaurants or hitting the gym.',
                    location: 'Los Angeles, CA',
                    occupation: 'Personal Trainer',
                    interests: ['Fitness', 'Cooking', 'Movies', 'Beach', 'Music'],
                    avatar: '👨',
                    photos: []
                },
                {
                    name: 'Sophia',
                    age: 26,
                    gender: 'female',
                    bio: 'Artist and yoga instructor. Believer in living life to the fullest and spreading positivity.',
                    location: 'Austin, TX',
                    occupation: 'Yoga Instructor',
                    interests: ['Yoga', 'Art', 'Meditation', 'Nature', 'Cooking'],
                    avatar: '🧘‍♀️',
                    photos: []
                },
                {
                    name: 'Michael',
                    age: 30,
                    gender: 'male',
                    bio: 'Tech entrepreneur who loves building things. Also a weekend musician and coffee snob.',
                    location: 'Seattle, WA',
                    occupation: 'Tech Entrepreneur',
                    interests: ['Technology', 'Music', 'Coffee', 'Startups', 'Travel'],
                    avatar: '👨‍💻',
                    photos: []
                },
                {
                    name: 'Olivia',
                    age: 29,
                    gender: 'female',
                    bio: 'Marketing professional with a passion for adventure. Love trying new things and meeting new people!',
                    location: 'New York, NY',
                    occupation: 'Marketing Manager',
                    interests: ['Travel', 'Fashion', 'Wine', 'Dancing', 'Photography'],
                    avatar: '💃',
                    photos: []
                },
                {
                    name: 'Daniel',
                    age: 27,
                    gender: 'male',
                    bio: 'Data scientist by day, gamer by night. Looking for someone who appreciates both intellect and fun.',
                    location: 'Boston, MA',
                    occupation: 'Data Scientist',
                    interests: ['Gaming', 'Data Science', 'Hiking', 'Board Games', 'Craft Beer'],
                    avatar: '🎮',
                    photos: []
                },
                {
                    name: 'Ava',
                    age: 25,
                    gender: 'female',
                    bio: 'Nurse with a big heart. Love helping others and making a difference. Also enjoy baking and running.',
                    location: 'Chicago, IL',
                    occupation: 'Registered Nurse',
                    interests: ['Running', 'Baking', 'Healthcare', 'Volunteering', 'Animals'],
                    avatar: '👩‍⚕️',
                    photos: []
                },
                {
                    name: 'Liam',
                    age: 31,
                    gender: 'male',
                    bio: 'Architect who loves design and creativity. Enjoy exploring new cities and finding hidden gems.',
                    location: 'Portland, OR',
                    occupation: 'Architect',
                    interests: ['Architecture', 'Design', 'Travel', 'Photography', 'Coffee'],
                    avatar: '🏗️',
                    photos: []
                }
            ];

            for (const profile of sampleProfiles) {
                await this.createProfile(profile);
            }

            console.log('Default data initialized successfully');
        } catch (error) {
            console.error('Error initializing default data:', error);
        }
    }

    // User preferences (stub - returns default preferences)
    async getUserPreferences(userId) {
        // For now, return default preferences
        return {
            ageMin: 18,
            ageMax: 99,
            genderPreference: 'all',
            maxDistance: 50
        };
    }

    // User interactions (stub - returns empty array for guest users)
    async getUserInteractions(userId) {
        if (!userId) return [];
        // TODO: Implement interactions tracking
        return [];
    }

    // Blocked users (stub - returns empty array)
    async getBlockedUsers(userId) {
        if (!userId) return [];
        // TODO: Implement blocking functionality
        return [];
    }

    // Add interaction (stub)
    async addInteraction(userId, profileId, type) {
        // TODO: Implement interaction tracking
        console.log(`Interaction: User ${userId} ${type} profile ${profileId}`);
        return { userId, profileId, type, timestamp: new Date().toISOString() };
    }

    // Check and create match (stub)
    async checkAndCelebrateMatch(userId, profileId) {
        // TODO: Implement real matching logic
        return null;
    }

    // Report user (stub)
    async reportUser(reporterId, reportedUserId, reason, details) {
        console.log(`Report: ${reporterId} reported ${reportedUserId} for ${reason}`);
        // TODO: Implement reporting
        return { reporterId, reportedUserId, reason, details, timestamp: new Date().toISOString() };
    }

    // Block user (stub)
    async blockUser(userId, blockedUserId, reason) {
        console.log(`Block: ${userId} blocked ${blockedUserId} for ${reason}`);
        // TODO: Implement blocking
        return { userId, blockedUserId, reason, timestamp: new Date().toISOString() };
    }

    // Clear all data
    async clearAllData() {
        const storeNames = ['users', 'profiles', 'matches', 'messages', 'likes', 'notifications'];
        const transaction = this.db.transaction(storeNames, 'readwrite');

        return Promise.all(storeNames.map(storeName => {
            const store = transaction.objectStore(storeName);
            return new Promise((resolve, reject) => {
                const request = store.clear();
                request.onsuccess = () => resolve();
                request.onerror = () => reject(request.error);
            });
        }));
    }
}
