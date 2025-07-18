from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import create_engine, text
from database import get_db, engine
from models import Base
from scheduler import start_trending_updater
import os
import logging
import traceback
import time
from datetime import datetime
from dotenv import load_dotenv

# Import route modules
from superadmin_routes import router as superadmin_router
from admin_routes import router as admin_router
from user_routes import get_user_routes
from tools_routes import get_tools_routes
from blogs_routes import router as blogs_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# Database connection test
def test_database_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

app = FastAPI(
    title="MarketMindAI API",
    description="Enhanced B2B Blogging and Tools Platform with AI Integration - Modular Architecture",
    version="2.0.0",
    debug=True
)

# Custom middleware for request logging and CORS debugging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    origin = request.headers.get('origin', 'No origin header')
    
    logger.info(f"Request: {request.method} {request.url} from origin: {origin}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(f"Response: {response.status_code} - Time: {process_time:.4f}s")
        
        # Add debugging headers
        response.headers["X-Request-ID"] = str(int(time.time() * 1000000))
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    except Exception as e:
        logger.error(f"Request failed: {e}")
        logger.error(traceback.format_exc())
        raise

# Get environment variables
FRONTEND_URL = os.getenv('APP_URL', 'http://localhost:3000')
BACKEND_URL = os.getenv('API_URL', 'http://localhost:8001')
CODESPACE_NAME = os.getenv('CODESPACE_NAME', '')

# Enhanced CORS middleware with comprehensive origins
allowed_origins = [
    # Local development
    "http://localhost:3000",
    "https://localhost:3000",
    "http://localhost:8001",
    "https://localhost:8001",
    "http://127.0.0.1:3000",
    "https://127.0.0.1:3000",
    
    # Environment variables
    FRONTEND_URL,
    BACKEND_URL,
    
    # Wildcard for development (NOT for production)
    "*"
]

# Add codespace-specific origins
if CODESPACE_NAME:
    allowed_origins.extend([
        f"https://{CODESPACE_NAME}-3000.app.github.dev",
        f"https://{CODESPACE_NAME}-8001.app.github.dev",
        f"https://{CODESPACE_NAME}-3000.preview.app.github.dev",
        f"https://{CODESPACE_NAME}-8001.preview.app.github.dev",
    ])

# Add all emergentagent.com subdomains
allowed_origins.extend([
    "https://fictional-happiness-jjgp7p5p4gp4hq9rw-3000.app.github.dev",
    "https://fictional-happiness-jjgp7p5p4gp4hq9rw-8001.app.github.dev",
    "https://5fb3398a-94d0-4c32-82e5-bf1dfe551dcb.preview.emergentagent.com",
])

# Dynamic pattern matching for emergentagent.com
import re
@app.middleware("http")
async def dynamic_cors(request: Request, call_next):
    origin = request.headers.get('origin')
    
    if origin:
        # Allow all emergentagent.com subdomains
        if re.match(r'https://.*\.emergentagent\.com$', origin):
            logger.info(f"Allowing emergentagent.com origin: {origin}")
            if origin not in allowed_origins:
                allowed_origins.append(origin)
        
        # Allow all github.dev subdomains
        if re.match(r'https://.*\.github\.dev$', origin):
            logger.info(f"Allowing github.dev origin: {origin}")
            if origin not in allowed_origins:
                allowed_origins.append(origin)
    
    response = await call_next(request)
    return response

# Remove duplicates and None values
allowed_origins = list(set(filter(None, allowed_origins)))
logger.info(f"Allowed CORS origins: {allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
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