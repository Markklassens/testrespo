from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
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

@router.post("/login", response_model=Token)
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
    return {"access_token": access_token, "token_type": "bearer"}

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
        # Don't reveal that the user doesn't exist
        return {"message": "If your email is registered, you will receive a password reset link"}
    
    reset_token = str(uuid.uuid4())
    user.reset_token = reset_token
    db.commit()
    
    # Send password reset email
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
    
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_verified_user)):
    return current_user

# User Profile and Settings Routes
user_router = APIRouter(prefix="/api/user", tags=["user"])

@user_router.put("/api-keys")
async def update_api_keys(
    keys: UserUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update user's API keys"""
    if keys.groq_api_key is not None:
        current_user.groq_api_key = keys.groq_api_key
    if keys.claude_api_key is not None:
        current_user.claude_api_key = keys.claude_api_key
    
    db.commit()
    return {"message": "API keys updated successfully"}

@user_router.put("/profile")
async def update_user_profile(
    profile_update: UserUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    update_data = profile_update.dict(exclude_unset=True)
    
    # Remove fields that users shouldn't be able to update themselves
    restricted_fields = ['user_type', 'is_active', 'is_verified']
    for field in restricted_fields:
        update_data.pop(field, None)
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated successfully"}

# AI Content Generation Routes
@user_router.post("/ai/generate-content")
async def generate_ai_content(
    request: AIContentRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Generate AI content using user's API keys"""
    
    # Set up AI manager with user's keys
    ai_manager.set_user_keys(current_user.groq_api_key, current_user.claude_api_key)
    
    try:
        result = await ai_manager.generate_content(
            prompt=request.prompt,
            content_type=request.content_type,
            provider=request.provider
        )
        
        # Save to database
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
        raise HTTPException(status_code=500, detail=str(e))

@user_router.get("/ai/content-history")
async def get_ai_content_history(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """Get user's AI content generation history"""
    from sqlalchemy import desc
    
    content_history = db.query(AIGeneratedContent).filter(
        AIGeneratedContent.user_id == current_user.id
    ).order_by(desc(AIGeneratedContent.created_at)).offset(skip).limit(limit).all()
    
    return content_history

@user_router.get("/dashboard-stats")
async def get_user_dashboard_stats(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for user"""
    from models import Blog, Review, Comment
    from sqlalchemy import func
    
    # User's content statistics
    user_blogs = db.query(Blog).filter(Blog.author_id == current_user.id).count()
    user_reviews = db.query(Review).filter(Review.user_id == current_user.id).count()
    user_comments = db.query(Comment).filter(Comment.user_id == current_user.id).count()
    
    # AI content statistics
    ai_content_count = db.query(AIGeneratedContent).filter(
        AIGeneratedContent.user_id == current_user.id
    ).count()
    
    # Recent activity
    recent_blogs = db.query(Blog).filter(Blog.author_id == current_user.id).order_by(
        desc(Blog.created_at)
    ).limit(5).all()
    
    recent_reviews = db.query(Review).filter(Review.user_id == current_user.id).order_by(
        desc(Review.created_at)
    ).limit(5).all()
    
    return {
        "content_stats": {
            "blogs": user_blogs,
            "reviews": user_reviews,
            "comments": user_comments,
            "ai_content": ai_content_count
        },
        "recent_activity": {
            "blogs": recent_blogs,
            "reviews": recent_reviews
        }
    }

# Include both routers
def get_user_routes():
    """Return combined user routes"""
    main_router = APIRouter()
    main_router.include_router(router)
    main_router.include_router(user_router)
    return main_router