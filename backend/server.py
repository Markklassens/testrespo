from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, func, desc, asc
from backend.database import get_db, engine
from backend.models import *
from backend.schemas import *
from backend.auth import *
from backend.ai_services import ai_manager
from backend.email_service import send_verification_email, send_password_reset_email, send_welcome_email
import uuid
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import csv
import io
import json
from typing import List, Optional
import math

load_dotenv()

app = FastAPI(
    title="MarketMindAI API",
    description="Enhanced B2B Blogging and Tools Platform with AI Integration",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "app": "MarketMindAI", "version": "2.0.0"}

# Authentication Routes
@app.post("/api/auth/register", response_model=UserResponse)
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

@app.post("/api/auth/login", response_model=Token)
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

@app.post("/api/auth/verify-email")
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

@app.post("/api/auth/request-password-reset")
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

@app.post("/api/auth/reset-password")
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

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_verified_user)):
    return current_user

# User API Key Management
@app.put("/api/auth/api-keys")
async def update_api_keys(
    keys: UserUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    if keys.groq_api_key is not None:
        current_user.groq_api_key = keys.groq_api_key
    if keys.claude_api_key is not None:
        current_user.claude_api_key = keys.claude_api_key
    
    db.commit()
    return {"message": "API keys updated successfully"}

# Enhanced Tools Routes with Advanced Filtering
@app.get("/api/tools/analytics")
async def get_tools_analytics(db: Session = Depends(get_db)):
    """Get tools analytics for landing page"""
    
    # Top trending tools
    trending_tools = db.query(Tool).order_by(desc(Tool.trending_score)).limit(10).all()
    
    # Top rated tools
    top_rated_tools = db.query(Tool).filter(Tool.total_reviews > 0).order_by(desc(Tool.rating)).limit(10).all()
    
    # Most viewed tools
    most_viewed_tools = db.query(Tool).order_by(desc(Tool.views)).limit(10).all()
    
    # Newest tools (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    newest_tools = db.query(Tool).filter(Tool.created_at >= thirty_days_ago).order_by(desc(Tool.created_at)).limit(10).all()
    
    # Featured tools
    featured_tools = db.query(Tool).filter(Tool.is_featured == True).limit(10).all()
    
    # Hot tools
    hot_tools = db.query(Tool).filter(Tool.is_hot == True).limit(10).all()
    
    return ToolAnalytics(
        trending_tools=trending_tools,
        top_rated_tools=top_rated_tools,
        most_viewed_tools=most_viewed_tools,
        newest_tools=newest_tools,
        featured_tools=featured_tools,
        hot_tools=hot_tools
    )

@app.get("/api/tools/search")
async def advanced_search_tools(
    q: Optional[str] = Query(None, description="Search query"),
    category_id: Optional[str] = Query(None),
    subcategory_id: Optional[str] = Query(None),
    pricing_model: Optional[str] = Query(None),
    company_size: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    employee_size: Optional[str] = Query(None),
    revenue_range: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    is_hot: Optional[bool] = Query(None),
    is_featured: Optional[bool] = Query(None),
    min_rating: Optional[float] = Query(None),
    sort_by: Optional[str] = Query("relevance"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Advanced search with pagination and filtering"""
    
    query = db.query(Tool)
    
    # Text search
    if q:
        search_filter = (
            Tool.name.ilike(f"%{q}%") | 
            Tool.description.ilike(f"%{q}%") |
            Tool.features.ilike(f"%{q}%") |
            Tool.short_description.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)
    
    # Apply filters
    if category_id:
        query = query.filter(Tool.category_id == category_id)
    if subcategory_id:
        query = query.filter(Tool.subcategory_id == subcategory_id)
    if pricing_model:
        query = query.filter(Tool.pricing_model == pricing_model)
    if company_size:
        query = query.filter(Tool.company_size == company_size)
    if industry:
        query = query.filter(Tool.industry == industry)
    if employee_size:
        query = query.filter(Tool.employee_size == employee_size)
    if revenue_range:
        query = query.filter(Tool.revenue_range == revenue_range)
    if location:
        query = query.filter(Tool.location.ilike(f"%{location}%"))
    if is_hot is not None:
        query = query.filter(Tool.is_hot == is_hot)
    if is_featured is not None:
        query = query.filter(Tool.is_featured == is_featured)
    if min_rating:
        query = query.filter(Tool.rating >= min_rating)
    
    # Sorting
    if sort_by == "rating":
        query = query.order_by(desc(Tool.rating))
    elif sort_by == "trending":
        query = query.order_by(desc(Tool.trending_score))
    elif sort_by == "views":
        query = query.order_by(desc(Tool.views))
    elif sort_by == "newest":
        query = query.order_by(desc(Tool.created_at))
    elif sort_by == "oldest":
        query = query.order_by(asc(Tool.created_at))
    elif sort_by == "name":
        query = query.order_by(asc(Tool.name))
    else:  # relevance
        query = query.order_by(desc(Tool.trending_score))
    
    # Get total count
    total = query.count()
    
    # Calculate pagination
    skip = (page - 1) * per_page
    tools = query.offset(skip).limit(per_page).all()
    
    total_pages = math.ceil(total / per_page)
    has_next = page < total_pages
    has_prev = page > 1
    
    return PaginatedToolsResponse(
        tools=tools,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )

@app.get("/api/categories/analytics")
async def get_category_analytics(db: Session = Depends(get_db)):
    """Get analytics for each category"""
    categories = db.query(Category).all()
    analytics = []
    
    for category in categories:
        tools_in_category = db.query(Tool).filter(Tool.category_id == category.id)
        tool_count = tools_in_category.count()
        
        if tool_count > 0:
            avg_rating = tools_in_category.with_entities(func.avg(Tool.rating)).scalar() or 0
            total_views = tools_in_category.with_entities(func.sum(Tool.views)).scalar() or 0
            recommended_tools = tools_in_category.order_by(desc(Tool.rating)).limit(5).all()
        else:
            avg_rating = 0
            total_views = 0
            recommended_tools = []
        
        analytics.append(CategoryAnalytics(
            category_id=category.id,
            category_name=category.name,
            tool_count=tool_count,
            avg_rating=float(avg_rating),
            total_views=int(total_views),
            recommended_tools=recommended_tools
        ))
    
    return analytics

# AI Content Generation Routes
@app.post("/api/ai/generate-content")
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

@app.get("/api/ai/content-history")
async def get_ai_content_history(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 20
):
    """Get user's AI content generation history"""
    
    content_history = db.query(AIGeneratedContent).filter(
        AIGeneratedContent.user_id == current_user.id
    ).order_by(desc(AIGeneratedContent.created_at)).offset(skip).limit(limit).all()
    
    return content_history

# Admin SEO Management Routes
@app.post("/api/admin/seo/optimize")
async def optimize_tool_seo(
    request: SEOOptimizationRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Generate SEO optimization for a tool (Admin only)"""
    
    tool = db.query(Tool).filter(Tool.id == request.tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    try:
        seo_result = await ai_manager.generate_seo_content(
            tool_name=tool.name,
            tool_description=tool.description,
            target_keywords=request.target_keywords,
            search_engine=request.search_engine
        )
        
        # Save SEO optimization
        seo_optimization = SEOOptimization(
            id=str(uuid.uuid4()),
            tool_id=tool.id,
            target_keywords=json.dumps(request.target_keywords),
            meta_title=seo_result["meta_title"],
            meta_description=seo_result["meta_description"],
            content=seo_result["content"],
            search_engine=request.search_engine,
            optimization_score=seo_result["optimization_score"],
            generated_by=seo_result["provider"]
        )
        
        db.add(seo_optimization)
        
        # Update tool with AI-generated SEO content
        tool.ai_meta_title = seo_result["meta_title"]
        tool.ai_meta_description = seo_result["meta_description"]
        tool.ai_content = seo_result["content"]
        
        db.commit()
        
        return SEOOptimizationResponse(
            meta_title=seo_result["meta_title"],
            meta_description=seo_result["meta_description"],
            content=seo_result["content"],
            optimization_score=seo_result["optimization_score"],
            keywords_used=request.target_keywords
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/seo/optimizations")
async def get_seo_optimizations(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Get all SEO optimizations (Admin only)"""
    
    optimizations = db.query(SEOOptimization).order_by(
        desc(SEOOptimization.created_at)
    ).offset(skip).limit(limit).all()
    
    return optimizations

# Keep all existing routes (categories, tools, blogs, reviews, etc.)
# ... [Previous route implementations remain the same] ...

# Categories Routes
@app.get("/api/categories", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return categories

@app.post("/api/categories", response_model=CategoryResponse)
async def create_category(
    category: CategoryCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    db_category = Category(
        id=str(uuid.uuid4()),
        name=category.name,
        description=category.description,
        icon=category.icon,
        color=category.color
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

# Subcategory Routes
@app.get("/api/subcategories", response_model=List[SubcategoryResponse])
async def get_subcategories(category_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Subcategory)
    if category_id:
        query = query.filter(Subcategory.category_id == category_id)
    subcategories = query.all()
    return subcategories

# Keep other existing routes...
# [Previous implementations for tools, blogs, reviews, comments, etc.]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)