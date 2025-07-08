# Production Configuration for MarketMindAI Backend
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import logging
from datetime import datetime

def configure_production_app(app: FastAPI):
    """Configure FastAPI app for production environment"""
    
    # Environment check
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    
    if is_production:
        # Add HTTPS redirect middleware
        app.add_middleware(HTTPSRedirectMiddleware)
        
        # Add trusted host middleware
        allowed_hosts = os.getenv("ALLOWED_HOSTS", "").split(",")
        if allowed_hosts and allowed_hosts[0]:
            app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    
    # Enhanced CORS configuration
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO" if is_production else "DEBUG")
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('/app/logs/app.log') if is_production else logging.StreamHandler(),
            logging.StreamHandler()
        ]
    )
    
    return app

# Security headers middleware
async def add_security_headers(request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# Rate limiting configuration
RATE_LIMIT_CONFIG = {
    "default": "100/minute",
    "auth": "5/minute",
    "upload": "10/minute"
}