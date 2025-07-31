from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import User, AIGeneratedContent
from schemas import *
from auth import (
    authenticate_user, create_access_token, get_current_verified_user,
    get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
)
from email_service import send_verification_email, send_password_reset_email, send_welcome_email
from ai_services import ai_manager
from typing import Optional
from datetime import datetime, timedelta
import uuid
import base64

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Authentication Routes
@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=400,
            detail="Username already taken"
        )
    
    # Create new user
    verification_token = str(uuid.uuid4())
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
        id=str(uuid.uuid4()),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password,
        user_type=user.user_type,
        verification_token=verification_token,
        is_active=True,
        is_verified=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send verification email
    if send_verification_email(user.email, user.full_name, verification_token):
        return db_user
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send verification email"
        )

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Email not verified"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Return both token and user data
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "user_type": user.user_type,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
            "groq_api_key": user.groq_api_key,
            "claude_api_key": user.claude_api_key
        }
    }

@router.post("/verify-email")
async def verify_email(verification: EmailVerification, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.verification_token == verification.token).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )
    
    user.is_verified = True
    user.verification_token = None
    db.commit()
    
    # Send welcome email
    send_welcome_email(user.email, user.full_name)
    
    return {"message": "Email verified successfully"}

@router.post("/request-password-reset")
async def request_password_reset(reset_request: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == reset_request.email).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Email not found"
        )
    
    # Generate reset token
    reset_token = str(uuid.uuid4())
    user.reset_token = reset_token
    db.commit()
    
    # Send reset email
    if send_password_reset_email(user.email, user.full_name, reset_token):
        return {"message": "Password reset email sent"}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to send password reset email"
        )

@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.reset_token == reset_data.token).first()
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_verified_user)):
    """Get current user profile"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    
    # Check if email is being changed and if it's already taken
    if user_update.full_name:
        current_user.full_name = user_update.full_name
    
    db.commit()
    db.refresh(current_user)
    return current_user

# NEW: API Keys Management Routes
@router.put("/api-keys")
async def update_api_keys(
    api_keys: APIKeysUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update user's AI API keys"""
    
    # Update API keys
    if api_keys.groq_api_key is not None:
        current_user.groq_api_key = api_keys.groq_api_key if api_keys.groq_api_key.strip() else None
    
    if api_keys.claude_api_key is not None:
        current_user.claude_api_key = api_keys.claude_api_key if api_keys.claude_api_key.strip() else None
    
    db.commit()
    db.refresh(current_user)
    
    return {"message": "API keys updated successfully"}

@router.get("/api-keys")
async def get_api_keys(current_user: User = Depends(get_current_verified_user)):
    """Get user's API keys status (masked for security)"""
    
    def mask_key(key):
        if not key:
            return None
        if len(key) <= 8:
            return key
        return key[:4] + "*" * (len(key) - 8) + key[-4:]
    
    return {
        "groq_api_key": mask_key(current_user.groq_api_key),
        "claude_api_key": mask_key(current_user.claude_api_key),
        "groq_configured": bool(current_user.groq_api_key),
        "claude_configured": bool(current_user.claude_api_key)
    }

# AI Content Generation Routes
@router.post("/generate-content", response_model=AIContentResponse)
async def generate_ai_content(
    request: AIContentRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Generate AI content using user's API keys"""
    
    # Check if user has at least one API key configured
    if not current_user.groq_api_key and not current_user.claude_api_key:
        raise HTTPException(
            status_code=400,
            detail="No AI API keys configured. Please add your Groq or Claude API key in profile settings."
        )
    
    try:
        # Use AI manager to generate content
        result = await ai_manager.generate_content(
            prompt=request.prompt,
            content_type=request.content_type,
            user_id=current_user.id,
            groq_key=current_user.groq_api_key,
            claude_key=current_user.claude_api_key,
            preferred_provider=request.provider
        )
        
        # Save generation history
        ai_content = AIGeneratedContent(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            content_type=request.content_type,
            prompt=request.prompt,
            generated_content=result["content"],
            provider=result["provider"],
            model=result.get("model", ""),
            tokens_used=result.get("tokens_used", 0)
        )
        
        db.add(ai_content)
        db.commit()
        
        return AIContentResponse(
            content=result["content"],
            provider=result["provider"],
            model=result.get("model", ""),
            tokens_used=result.get("tokens_used", 0)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate content: {str(e)}"
        )

@router.get("/ai-usage")
async def get_ai_usage_stats(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get user's AI usage statistics"""
    
    # Get usage statistics
    total_generations = db.query(AIGeneratedContent).filter(
        AIGeneratedContent.user_id == current_user.id
    ).count()
    
    recent_generations = db.query(AIGeneratedContent).filter(
        AIGeneratedContent.user_id == current_user.id
    ).order_by(desc(AIGeneratedContent.created_at)).limit(10).all()
    
    return {
        "total_generations": total_generations,
        "recent_generations": recent_generations,
        "api_keys_configured": {
            "groq": bool(current_user.groq_api_key),
            "claude": bool(current_user.claude_api_key)
        }
    }

def get_user_routes():
    """Return user routes router"""
    return router