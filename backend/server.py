from fastapi import FastAPI, HTTPException, Request, Response, Depends
from sqlalchemy.orm import Session
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
import os
os.makedirs('/tmp/logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/logs/backend.log'),
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
    "https://c6069ed4-660b-4e82-ac07-634cd9a68a6f.preview.emergentagent.com",
    "https://psychic-space-potato-x54gpgwg9pw626rpp-3000.app.github.dev",
    "https://psychic-space-potato-x54gpgwg9pw626rpp-8001.app.github.dev",
])

# Enhanced dynamic pattern matching for any github.dev and emergentagent.com domains
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
        
        # Allow all app.github.dev subdomains 
        if re.match(r'https://.*\.app\.github\.dev$', origin):
            logger.info(f"Allowing app.github.dev origin: {origin}")
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

# Test database connection on startup
if test_database_connection():
    logger.info("Database connection verified successfully")
else:
    logger.error("Database connection failed during startup")

# Start the trending updater background task
start_trending_updater()

# Enhanced health check endpoint with database connectivity
@app.get("/api/health")
async def health_check():
    health_status = {
        "status": "healthy",
        "app": "MarketMindAI",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "database": "disconnected",
        "services": {
            "api": "healthy",
            "database": "disconnected",
            "scheduler": "running"
        }
    }
    
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone():
                health_status["database"] = "connected"
                health_status["services"]["database"] = "connected"
                health_status["status"] = "healthy"
    except Exception as e:
        logger.error(f"Health check database error: {e}")
        health_status["database"] = f"error: {str(e)}"
        health_status["services"]["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"
    
    return health_status

# Debug endpoint for connectivity testing
@app.get("/api/debug/connectivity")
async def debug_connectivity():
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "DATABASE_URL": bool(os.getenv("DATABASE_URL")),
            "FRONTEND_URL": FRONTEND_URL,
            "BACKEND_URL": BACKEND_URL,
            "CODESPACE_NAME": CODESPACE_NAME or "Not set"
        },
        "cors_origins": allowed_origins,
        "database_test": "failed",
        "recent_logs": []
    }
    
    # Test database connection
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            user_count = result.fetchone()[0]
            debug_info["database_test"] = "success"
            debug_info["database_info"] = {
                "user_count": user_count,
                "engine_pool_size": engine.pool.size(),
                "engine_pool_checked_in": engine.pool.checkedin(),
                "engine_pool_checked_out": engine.pool.checkedout()
            }
    except Exception as e:
        debug_info["database_test"] = f"error: {str(e)}"
        debug_info["database_error"] = str(e)
    
    return debug_info

# Enhanced CORS preflight endpoint
@app.options("/api/{path:path}")
async def cors_preflight(path: str, request: Request):
    origin = request.headers.get('origin', '*')
    
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",
            "Vary": "Origin"
        }
    )

# Include route modules
app.include_router(superadmin_router, prefix="", tags=["superadmin"])
app.include_router(admin_router, prefix="", tags=["admin"])
app.include_router(get_user_routes(), prefix="", tags=["user", "authentication"])
app.include_router(get_tools_routes(), prefix="", tags=["tools", "free-tools"])
app.include_router(blogs_router, prefix="", tags=["blogs"])

# Global Categories Route
@app.get("/api/categories")
async def get_categories_global(db: Session = Depends(get_db)):
    """Get all categories - Global endpoint"""
    from models import Category
    categories = db.query(Category).all()
    return categories

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