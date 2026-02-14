# LoveAI - AI-Powered Dating App 💕

A fully functional, AI-powered dating application built with vanilla JavaScript, IndexedDB, and OpenAI's GPT-4 API.

![LoveAI Dating App](https://img.shields.io/badge/Version-2.0-purple) ![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow) ![AI Powered](https://img.shields.io/badge/AI-GPT--4-blue)

## ✨ Features

### Core Dating Features
- **🔍 Swipe Discovery Interface**: Tinder-like swipe interface to browse profiles
- **🤖 AI-Powered Matching**: GPT-4 integration for intelligent compatibility scoring
- **💬 Real-Time Messaging**: Chat with your matches instantly
- **❤️ Match Detection**: Automatic mutual match detection with celebration animation
- **👤 User Profiles**: Complete profile creation with photos, bio, interests, and preferences
- **🔔 Notifications**: Real-time notifications for matches, messages, and likes

### AI Features (with OpenAI API Key)
- **Smart Compatibility Analysis**: AI analyzes profiles and provides detailed compatibility scores with reasons
- **Conversation Starters**: AI generates personalized ice-breakers based on profiles
- **Bio Suggestions**: AI helps create engaging profile bios
- **Pattern Analysis**: AI provides insights into dating behavior and tips

### Safety & Privacy
- **🛡️ Block Users**: Block unwanted users
- **⚠️ Report Profiles**: Report inappropriate behavior
- **📋 Safety Tips**: Built-in safety guidelines
- **🔒 Privacy Controls**: Control who can see your profile

### Additional Features
- **✅ Onboarding Flow**: Guided setup for new users
- **📸 Photo Upload**: Support for multiple profile photos (up to 6)
- **🏷️ Interest Tags**: Select from common interests or add custom ones
- **⚙️ Advanced Preferences**: Filter by age, distance, and gender
- **📊 Match Management**: View all matches in one place
- **👨‍💼 Admin Panel**: Admin tools for managing the platform

## 🚀 Quick Start

### 1. Installation

No installation required! This is a client-side application.

1. Clone or download this repository
2. Open `index.html` in a modern web browser (Chrome, Firefox, Safari, Edge)

### 2. Demo Credentials

**Option A: Use Demo Accounts**
- **Admin**: `admin@loveai.com` / `admin123`
- **User**: `user@loveai.com` / `user123`

**Option B: Create New Account**
1. Click "Sign up" on the login screen
2. Fill in your details (must be 18+)
3. Complete the onboarding flow

### 3. Enable AI Features (Optional)

1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Log in to the app
3. Navigate to Settings (⚙️)
4. Scroll to "AI Settings"
5. Enter your API key
6. Click "Save API Key" and then "Test Connection"

**Without API Key**: Simple fallback compatibility algorithm
**With API Key**: GPT-4 powered matching, conversation starters, and bio suggestions

## 📱 Usage Guide

### Creating Your Profile

1. After login, complete the onboarding:
   - Choose avatar emoji or upload photos
   - Write your bio (or use AI suggestions)
   - Add occupation and location
   - Select interests (minimum 3)
   - Set discovery preferences

### Discovering Matches

1. Go to **Discover** tab (🔍)
2. Swipe right (❤️) to like, left (✕) to pass
3. Tap star (⭐) for Super Like
4. View profile details by scrolling down

### When You Match

1. "It's a Match!" celebration appears
2. Send a message or keep swiping
3. View all matches in **Matches** tab (❤️)

### Messaging

1. Go to **Messages** tab (💬)
2. Tap on a match to open chat
3. AI conversation starters appear for new matches

## 🏗️ Project Structure

```
loveai-app/
├── index.html              # Main HTML file
├── styles.css              # All styling
├── js/
│   ├── app.js             # Main app initialization & navigation
│   ├── database.js        # IndexedDB management (1164 lines)
│   ├── ai-matching.js     # AI matching engine with ChatGPT
│   ├── auth.js            # Authentication logic
│   ├── profiles.js        # Profile browsing & display
│   ├── discovery.js       # Swipe interface & discovery
│   ├── matches.js         # Match detection & celebration
│   ├── messaging.js       # Real-time messaging system
│   ├── notifications.js   # Notification system
│   ├── settings.js        # User settings & preferences
│   ├── onboarding.js      # New user onboarding flow
│   ├── admin.js           # Admin panel functionality
│   └── utils.js           # Utility functions
└── README.md              # This file
```

## 💾 Database Schema

### Object Stores
1. **users**: User accounts and authentication
2. **profiles**: Dating profiles with photos and interests
3. **interactions**: Like/pass history
4. **matches**: Mutual matches
5. **messages**: Chat messages
6. **notifications**: User notifications
7. **blocked_users**: Blocked user list
8. **reports**: User reports
9. **user_preferences**: User settings and preferences

## 🔧 Tech Stack

- **Frontend**: Vanilla JavaScript (ES6+)
- **Database**: IndexedDB (client-side, offline-capable)
- **Authentication**: Custom auth with SHA-256 password hashing
- **AI**: OpenAI GPT-4 API
- **Storage**: LocalStorage for sessions, IndexedDB for data
- **Security**: Web Crypto API

## 🛠️ Development

### Adding New Features

1. **New Database Store**: Edit `js/database.js` → Update `dbVersion` and add in `onupgradeneeded`
2. **New Screen**: Add HTML in `index.html` and create corresponding JS file
3. **New Styles**: Add to `styles.css`
4. **Navigation**: Update `showScreen()` in `app.js`

## 🔍 Testing

**Manual Testing Checklist:**
- ✅ Create new account
- ✅ Complete onboarding
- ✅ Like profiles & match
- ✅ Send messages
- ✅ Receive notifications
- ✅ Update profile
- ✅ Change settings
- ✅ Block/report users
- ✅ Admin panel

## 🐛 Troubleshooting

### Database Issues
**Problem**: Login fails or "User not found"
**Solution**:
1. Open DevTools (F12) → Application → Storage
2. Clear storage
3. Refresh page

### API Issues
**Problem**: AI features not working
**Solution**:
1. Verify API key in Settings
2. Click "Test Connection"
3. Check browser console for errors
4. Ensure you have OpenAI API credits

### Photo Upload Issues
**Problem**: Photos not uploading
**Solution**:
1. Keep photos under 5MB
2. Use JPG/PNG formats
3. Try fewer photos at once

## 📈 Future Enhancements

1. **Backend Integration**: Node.js/Express for real multi-user functionality
2. **Real-Time Sync**: WebSocket support for instant messaging
3. **Push Notifications**: Browser push notifications
4. **Video Chat**: WebRTC integration
5. **Verification System**: Profile verification badges
6. **Premium Features**: Boost, rewind, unlimited likes
7. **Location Services**: Real geolocation-based matching
8. **Analytics Dashboard**: Advanced insights

## ⚠️ Limitations

- **Client-Side Only**: All data is local to the browser
- **No Real-Time Sync**: No cross-device synchronization
- **No Backend**: Cannot connect multiple users in real-time
- **Photo Storage**: Photos stored as base64 (5MB limit)

## 🌐 Browser Compatibility

**Minimum Requirements:**
- Chrome 87+
- Firefox 78+
- Safari 14+
- Edge 87+

**Required APIs:**
- IndexedDB
- Web Crypto API
- LocalStorage
- ES6+ JavaScript

## 📄 License

Open-source for educational purposes.

## 💬 Support

For issues:
1. Check troubleshooting section
2. Review browser console
3. Verify browser compatibility
4. Check API key (if using AI features)

---

**Note**: This is a demonstration application. For production use, implement proper backend infrastructure, real authentication, encrypted data storage, and comply with privacy regulations (GDPR, CCPA, etc.).

Made with ❤️ and AI

Enjoy your AI-powered dating experience! 🎉