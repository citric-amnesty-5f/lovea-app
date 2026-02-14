"""
Main FastAPI application
"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.database import init_db, get_db
from app.routers import (
    auth_routes,
    profile_routes,
    discovery_routes,
    messaging_routes,
    admin_routes
)

# Create FastAPI app
app = FastAPI(
    title="LoveAI API",
    description="AI-Powered Dating App Backend with GPT-4 Matchmaking",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
# Note: Cannot use "*" with allow_credentials=True, so we list specific origins
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5500",  # Live Server
    "http://10.0.0.124:3000",  # Local network IP
    "https://calyciform-undiffusively-jedidiah.ngrok-free.dev",  # ngrok backend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # Allow common development origins (LAN IPs and ngrok) without per-IP edits.
    allow_origin_regex=r"^https?://("
                       r"localhost|127\.0\.0\.1|"
                       r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
                       r"192\.168\.\d{1,3}\.\d{1,3}|"
                       r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|"
                       r".+\.ngrok-free\.(app|dev)|"
                       r".+\.ngrok\.io"
                       r")(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting LoveAI API...")
    init_db()
    print("✅ Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Shutting down LoveAI API...")


# ============================================================================
# Include Routers
# ============================================================================

app.include_router(auth_routes.router)
app.include_router(profile_routes.router)
app.include_router(discovery_routes.router)
app.include_router(messaging_routes.router)
app.include_router(admin_routes.router)


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Welcome to LoveAI API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "LoveAI API",
        "version": "1.0.0"
    }


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
