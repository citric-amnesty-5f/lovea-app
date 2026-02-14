"""
Main FastAPI application
"""
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uvicorn

from app.database import init_db
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

env_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
origins.extend(env_origins)

origin_regex = os.getenv(
    "ALLOWED_ORIGIN_REGEX",
    r"^https?://("
    r"localhost|127\.0\.0\.1|"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|"
    r".+\.ngrok-free\.(app|dev)|"
    r".+\.ngrok\.io|"
    r".+\.onrender\.com"
    r")(:\d+)?$",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
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

# Optional: serve built frontend from this backend process (single-URL mode).
SERVE_FRONTEND = os.getenv("SERVE_FRONTEND", "false").lower() == "true"
FRONTEND_DIST_DIR = Path(__file__).resolve().parents[2] / "dist"


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/")
async def root():
    """API root endpoint"""
    if SERVE_FRONTEND:
        index_file = FRONTEND_DIST_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)

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


# Serve static frontend assets for unknown paths when enabled.
if SERVE_FRONTEND:
    if FRONTEND_DIST_DIR.exists():
        FRONTEND_DIST_DIR = FRONTEND_DIST_DIR.resolve()

        @app.get("/{full_path:path}", include_in_schema=False)
        async def serve_frontend(full_path: str):
            if full_path:
                candidate = (FRONTEND_DIST_DIR / full_path).resolve()
                if FRONTEND_DIST_DIR in candidate.parents and candidate.is_file():
                    return FileResponse(candidate)

            index_file = FRONTEND_DIST_DIR / "index.html"
            if index_file.exists():
                return FileResponse(index_file)

            raise HTTPException(status_code=404, detail="Frontend build not found")
    else:
        print(f"⚠ SERVE_FRONTEND is enabled but dist directory is missing: {FRONTEND_DIST_DIR}")


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
