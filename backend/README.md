# LoveAI Backend API 🚀

Production-ready FastAPI backend for LoveAI dating app with AI-powered matchmaking, real-time chat, and comprehensive user management.

## 🌟 Features

### Core Features
- ✅ **JWT Authentication** - Secure token-based auth with bcrypt password hashing
- ✅ **User Registration & Login** - Complete user lifecycle management
- ✅ **Profile Management** - Rich profiles with photos, interests, and preferences
- ✅ **AI Matchmaking** - OpenAI GPT-4 powered compatibility analysis
- ✅ **Real-time Chat** - WebSocket-based messaging with typing indicators
- ✅ **Admin Dashboard** - Complete admin panel with statistics and moderation
- ✅ **Content Moderation** - AI-powered safety checks on messages
- ✅ **Role-Based Access Control** - User, Moderator, Admin roles

### AI Capabilities
- 🤖 **Compatibility Scoring** - AI analyzes profiles for compatibility
- 💬 **Conversation Starters** - Personalized ice breakers for matches
- ✍️ **Bio Generation** - AI helps users create engaging bios
- 🛡️ **Content Safety** - Automatic flagging of inappropriate content

### Technical Features
- 🗄️ **PostgreSQL Database** - Robust relational database
- 📊 **SQLAlchemy ORM** - Type-safe database operations
- 🔄 **Alembic Migrations** - Database version control
- 🌐 **WebSocket Support** - Real-time bidirectional communication
- 📝 **Auto-generated API Docs** - Interactive Swagger/ReDoc documentation
- 🔒 **Security** - Password hashing, JWT tokens, CORS protection

## 🏗️ Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Authentication & authorization
│   ├── routers/
│   │   ├── auth_routes.py   # Login, register, logout
│   │   ├── profile_routes.py # Profile management
│   │   ├── discovery_routes.py # Matching & discovery
│   │   ├── messaging_routes.py # Chat & WebSocket
│   │   └── admin_routes.py  # Admin endpoints
│   └── services/
│       └── ai_service.py    # OpenAI integration
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── init_db.py              # Database initialization script
└── README.md               # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- OpenAI API key (for AI features)

### 1. Install Dependencies

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/loveai_db
SECRET_KEY=your-super-secret-key-min-32-chars
OPENAI_API_KEY=sk-your-openai-api-key
```

### 3. Setup Database

#### Option A: Automated Setup (Recommended)
```bash
# Create database
createdb loveai_db

# Initialize with sample data
python init_db.py
```

This creates:
- All database tables
- 20 sample interests
- Admin user: `admin@loveai.com` / `admin123`
- 20 demo users: `user1@loveai.com` through `user20@loveai.com` / `user123`

#### Option B: Manual Setup
```bash
# Create database
createdb loveai_db

# Run migrations
alembic upgrade head
```

### 4. Run Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or use the main.py directly
python -m app.main
```

Server runs at: `http://localhost:8000`

### 5. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 API Endpoints

### Authentication
```
POST   /auth/register       - Register new user
POST   /auth/login          - Login
POST   /auth/logout         - Logout
GET    /auth/me             - Get current user
POST   /auth/verify-token   - Verify JWT token
```

### Profiles
```
GET    /profiles/me         - Get own profile
PUT    /profiles/me         - Update own profile
GET    /profiles/{user_id}  - Get user profile
POST   /profiles/me/interests - Add interests
DELETE /profiles/me/interests/{id} - Remove interest
POST   /profiles/me/photos  - Add photo
DELETE /profiles/me/photos/{id} - Delete photo
GET    /profiles/me/preferences - Get preferences
PUT    /profiles/me/preferences - Update preferences
```

### Discovery & Matching
```
GET    /discovery/profiles  - Get profiles to swipe
POST   /discovery/interact  - Like/Pass/Super Like
GET    /discovery/matches   - Get all matches
DELETE /discovery/matches/{id} - Unmatch
```

### Messaging
```
WS     /messages/ws         - WebSocket connection
POST   /messages/           - Send message (HTTP)
GET    /messages/conversations - Get all conversations
GET    /messages/conversations/{id} - Get specific conversation
PUT    /messages/conversations/{id}/read - Mark as read
```

### Admin (Requires Admin/Moderator Role)
```
GET    /admin/users         - List all users
GET    /admin/users/{id}    - Get user details
PUT    /admin/users/{id}/activate - Activate user
PUT    /admin/users/{id}/deactivate - Deactivate user
PUT    /admin/users/{id}/role - Change user role
DELETE /admin/users/{id}    - Delete user
GET    /admin/reports       - Get user reports
PUT    /admin/reports/{id}/resolve - Resolve report
GET    /admin/stats/users   - User statistics
GET    /admin/stats/ai      - AI usage statistics
GET    /admin/moderation/flagged-messages - Flagged messages
```

## 🔐 Authentication

### Registration
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123",
    "name": "Test User",
    "date_of_birth": "1995-06-15",
    "gender": "male"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123"
  }'
```

Returns:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": 1,
  "role": "user"
}
```

### Using Token
```bash
curl -X GET http://localhost:8000/profiles/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 💬 WebSocket Chat

### Connect
```javascript
const ws = new WebSocket('ws://localhost:8000/messages/ws?token=YOUR_JWT_TOKEN');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Send Message
```javascript
ws.send(JSON.stringify({
  type: 'send_message',
  match_id: 1,
  content: 'Hello!'
}));
```

### Typing Indicator
```javascript
ws.send(JSON.stringify({
  type: 'typing',
  match_id: 1,
  is_typing: true
}));
```

### Mark as Read
```javascript
ws.send(JSON.stringify({
  type: 'mark_read',
  match_id: 1
}));
```

## 🗄️ Database Schema

### Main Tables
- **users** - User accounts and authentication
- **profiles** - Dating profiles
- **interests** - Available interests
- **photos** - Profile photos
- **preferences** - Dating preferences
- **interactions** - Likes, passes, super likes
- **matches** - Mutual matches
- **messages** - Chat messages
- **notifications** - User notifications
- **blocks** - Blocked users
- **reports** - User reports
- **ai_logs** - AI API usage tracking

### Relationships
```
User 1:1 Profile
Profile N:M Interests
Profile 1:1 Preferences
User 1:N Interactions (sent/received)
Match N:N Users (user1, user2)
Match 1:N Messages
User 1:N Notifications
```

## 🤖 AI Integration

### Compatibility Analysis
```python
from app.services.ai_service import AIService

ai_service = AIService(db)
score, reasons, ice_breakers = await ai_service.calculate_compatibility(
    profile1, profile2
)
```

Returns:
- `score`: 0-100 compatibility score
- `reasons`: List of why they're compatible
- `ice_breakers`: Personalized conversation starters

### Bio Generation
```python
bio_response = await ai_service.generate_bio_suggestions(
    name="John",
    age=28,
    gender="male",
    occupation="Software Engineer",
    interests=["hiking", "photography", "cooking"]
)
```

### Content Moderation
```python
safety_score, is_safe = await ai_service.moderate_content(
    "Message content",
    content_type="message"
)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `SECRET_KEY` | JWT secret key (min 32 chars) | Required |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Optional |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration time | 10080 (7 days) |
| `SQL_ECHO` | Enable SQL query logging | false |
| `DEBUG` | Enable debug mode | true |

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/test_auth.py
```

## 📊 Admin Features

### User Statistics
```bash
curl -X GET http://localhost:8000/admin/stats/users \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

Returns:
```json
{
  "total_users": 100,
  "active_users": 85,
  "verified_users": 60,
  "total_matches": 250,
  "total_messages": 1500,
  "new_users_today": 5,
  "new_matches_today": 12
}
```

### AI Usage Statistics
```bash
curl -X GET http://localhost:8000/admin/stats/ai?days=7 \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## 🚦 Production Deployment

### 1. Update Configuration
```env
DEBUG=false
DATABASE_URL=postgresql://prod_user:prod_pass@prod_host:5432/prod_db
SECRET_KEY=super-secure-production-key
```

### 2. Run with Production Server
```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

### 3. Use PostgreSQL Connection Pooling
- Configure PgBouncer or use managed database

### 4. Add Redis for Caching (Optional)
- Cache frequently accessed profiles
- Store WebSocket connections
- Session management

### 5. Enable HTTPS
- Use nginx reverse proxy
- Configure SSL certificates

## 🔒 Security Best Practices

1. **Password Security**
   - Minimum 8 characters
   - Requires uppercase, lowercase, and digit
   - Bcrypt hashing with salt

2. **JWT Tokens**
   - 7-day expiration
   - HMAC SHA-256 signing
   - Include user_id, email, role

3. **Role-Based Access**
   - User: Standard access
   - Moderator: Content moderation
   - Admin: Full system access

4. **Content Moderation**
   - AI-powered message scanning
   - Automatic flagging system
   - Manual review by moderators

5. **Rate Limiting** (Add in production)
   - Implement request throttling
   - Prevent API abuse

## 📈 Performance Optimization

1. **Database**
   - Index on frequently queried fields
   - Connection pooling
   - Query optimization

2. **Caching**
   - Cache user profiles
   - Cache AI responses
   - Use Redis for session storage

3. **AI Requests**
   - Batch compatibility calculations
   - Cache AI results
   - Use cheaper models where appropriate

4. **WebSocket**
   - Connection management
   - Heartbeat/ping-pong
   - Reconnection handling

## 🐛 Troubleshooting

### Database Connection Error
```
sqlalchemy.exc.OperationalError: could not connect to server
```
**Solution**: Check DATABASE_URL and ensure PostgreSQL is running

### OpenAI API Error
```
openai.error.AuthenticationError: Incorrect API key
```
**Solution**: Verify OPENAI_API_KEY in .env

### WebSocket Connection Failed
```
WebSocket connection failed: token invalid
```
**Solution**: Ensure JWT token is valid and passed in query params

### Import Errors
```
ModuleNotFoundError: No module named 'app'
```
**Solution**: Run from backend/ directory or set PYTHONPATH

## 📝 License

MIT License - see LICENSE file

## 👥 Contributors

Built with ❤️ for the LoveAI project

## 🤝 Support

For issues and questions:
- Check the documentation
- Review API docs at `/docs`
- Check logs for errors

---

**Happy Coding! 💕**
