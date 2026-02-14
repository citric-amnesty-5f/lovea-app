# LoveAI Backend - Quick Start Guide ⚡

Get the backend running in **5 minutes**!

## Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Git (optional)

## 🚀 Fast Setup (5 Steps)

### Step 1: Install Dependencies (1 min)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Setup PostgreSQL (1 min)
```bash
# Create database
createdb loveai_db
```

### Step 3: Configure Environment (30 seconds)
```bash
cp .env.example .env
```

Edit `.env` and set (minimum):
```env
DATABASE_URL=postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/loveai_db
SECRET_KEY=change-this-to-a-random-32-char-string
OPENAI_API_KEY=sk-your-openai-key-optional
```

### Step 4: Initialize Database (30 seconds)
```bash
python init_db.py
```

This creates:
- All database tables
- Admin user: `admin@loveai.com` / `admin123`
- 20 demo users: `user1@loveai.com` - `user20@loveai.com` / `user123`
- 20 sample interests

### Step 5: Start Server (10 seconds)
```bash
uvicorn app.main:app --reload
```

## ✅ Verify It Works

### Test 1: Open API Docs
Visit: http://localhost:8000/docs

You should see interactive API documentation.

### Test 2: Health Check
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "LoveAI API",
  "version": "1.0.0"
}
```

### Test 3: Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user1@loveai.com",
    "password": "user123"
  }'
```

Should return a JWT token.

### Test 4: Run Full Test Suite
```bash
python test_api.py
```

Should pass all 8 tests.

## 🎉 You're Done!

The backend is now running at: **http://localhost:8000**

## 📚 Next Steps

1. **Explore API Docs**: http://localhost:8000/docs
2. **Read Full Documentation**: `README.md`
3. **Connect Frontend**: Update frontend to use API instead of IndexedDB
4. **Add OpenAI Key**: For AI matchmaking features

## 🐳 Alternative: Docker Setup

Even faster with Docker!

```bash
# 1. Set environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# 2. Start everything
docker-compose up -d

# 3. Initialize database
docker-compose exec backend python init_db.py

# 4. Done!
open http://localhost:8000/docs
```

## 🔑 Login Credentials

**Admin:**
- Email: `admin@loveai.com`
- Password: `admin123`
- Access: Full admin panel

**Demo Users:**
- Email: `user1@loveai.com` through `user20@loveai.com`
- Password: `user123`
- Access: Standard user features

## 🆘 Troubleshooting

**Problem: Database connection error**
```
Solution: Check DATABASE_URL in .env matches your PostgreSQL setup
```

**Problem: ImportError**
```
Solution: Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

**Problem: Port 8000 already in use**
```
Solution: Kill process or use different port
uvicorn app.main:app --reload --port 8001
```

**Problem: init_db.py fails**
```
Solution: Drop and recreate database
dropdb loveai_db && createdb loveai_db && python init_db.py
```

## 📞 Get Help

1. Check error message in terminal
2. Review `README.md` for detailed docs
3. Check `/docs` endpoint for API reference
4. Verify PostgreSQL is running: `pg_isready`

---

**Happy Coding! 💕**
