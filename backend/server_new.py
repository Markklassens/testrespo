from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from database import get_db, engine
from models import Base
from scheduler import start_trending_updater
import os
from dotenv import load_dotenv

# Import route modules
from superadmin_routes import router as superadmin_router
from admin_routes import router as admin_router
from user_routes import get_user_routes
from tools_routes import get_tools_routes
from blogs_routes import router as blogs_router

load_dotenv()

app = FastAPI(
    title="MarketMindAI API",
    description="Enhanced B2B Blogging and Tools Platform with AI Integration - Modular Architecture",
    version="2.0.0"
)

# Get environment variables
FRONTEND_URL = os.getenv('APP_URL', 'http://localhost:3000')
BACKEND_URL = os.getenv('API_URL', 'http://localhost:8001')
CODESPACE_NAME = os.getenv('CODESPACE_NAME', '')

# CORS middleware with comprehensive origins
allowed_origins = [
    "http://localhost:3000",
    "https://localhost:3000",
    "http://localhost:8001",
    "https://localhost:8001",
    FRONTEND_URL,
    BACKEND_URL,
]

# Add codespace-specific origins
if CODESPACE_NAME:
    allowed_origins.extend([
        f"https://{CODESPACE_NAME}-3000.app.github.dev",
        f"https://{CODESPACE_NAME}-8001.app.github.dev",
    ])

# Add common development origins
additional_origins = [
    "https://fictional-happiness-jjgp7p5p4gp4hq9rw-3000.app.github.dev",
    "https://fictional-happiness-jjgp7p5p4gp4hq9rw-8001.app.github.dev",
    "https://96c19268-7ccd-42f7-9fb8-40015993c1c5.preview.emergentagent.com",
]
allowed_origins.extend(additional_origins)

# Remove duplicates and None values
allowed_origins = list(set(filter(None, allowed_origins)))
print(f"Allowed CORS origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Start the trending updater background task
start_trending_updater()

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": "MarketMindAI", "version": "2.0.0"}

# Include route modules
app.include_router(superadmin_router, prefix="", tags=["superadmin"])
app.include_router(admin_router, prefix="", tags=["admin"])
app.include_router(get_user_routes(), prefix="", tags=["user", "authentication"])
app.include_router(get_tools_routes(), prefix="", tags=["tools", "free-tools"])
app.include_router(blogs_router, prefix="", tags=["blogs"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "MarketMindAI API - Modular Architecture",
        "version": "2.0.0",
        "modules": [
            "superadmin",
            "admin", 
            "user",
            "tools",
            "blogs"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)