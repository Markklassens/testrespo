from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Query, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, func, desc, asc
from database import get_db, engine
from models import *
from schemas import *
from auth import *
from ai_services import ai_manager
from email_service import send_verification_email, send_password_reset_email, send_welcome_email
from search_service import search_service
from trending_calculator import update_trending_scores, get_trending_analytics, increment_view_and_update_trending
from scheduler import start_trending_updater, manual_update
import uuid
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import csv
import io
import json
from typing import List, Optional
import math
from jose import JWTError, jwt

load_dotenv()

app = FastAPI(
    title="MarketMindAI API",
    description="Enhanced B2B Blogging and Tools Platform with AI Integration",
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
    "https://c7c4f69f-b4ca-4e4d-a8f1-f3342f697ca7.preview.emergentagent.com",
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
@app.put("/api/admin/tools/{tool_id}/content", response_model=ToolResponse)
async def update_tool_content(
    tool_id: str,
    content_update: ToolUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update tool content (Admin only - must have access to tool)"""
    from auth import check_tool_access
    
    # Check if admin has access to this tool
    if not check_tool_access(current_user, tool_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this tool. Please request access from a superadmin."
        )
    
    db_tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not db_tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Only allow specific fields to be updated by regular admins
    allowed_fields = [
        'description', 'short_description', 'features', 'pricing_details',
        'meta_title', 'meta_description', 'ai_meta_title', 'ai_meta_description', 'ai_content'
    ]
    
    update_data = content_update.dict(exclude_unset=True)
    
    # If regular admin, restrict fields
    if current_user.user_type == "admin":
        update_data = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    for field, value in update_data.items():
        setattr(db_tool, field, value)
    
    db.commit()
    db.refresh(db_tool)
    return db_tool

@app.get("/api/tools/analytics")
async def get_tools_analytics(
    recalculate: bool = False,
    db: Session = Depends(get_db)
):
    """Get tools analytics for landing page with optional recalculation"""
    
    # Always recalculate trending scores to ensure fresh data
    analytics = get_trending_analytics(db, recalculate=True)
    
    # Convert to the expected response format
    from schemas import ToolAnalytics
    return ToolAnalytics(
        trending_tools=analytics["trending_tools"],
        top_rated_tools=analytics["top_rated_tools"],
        most_viewed_tools=analytics["most_viewed_tools"],
        newest_tools=analytics["newest_tools"],
        featured_tools=analytics["featured_tools"],
        hot_tools=analytics["hot_tools"]
    )

@app.post("/api/admin/tools/update-trending")
async def update_tools_trending_scores(
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Update trending scores for all tools (Super Admin only)"""
    
    result = update_trending_scores(db)
    return {
        "message": "Trending scores updated successfully",
        "details": result
    }

@app.post("/api/admin/tools/update-trending-manual")
async def manual_update_trending(
    current_user: User = Depends(require_superadmin)
):
    """Manually trigger trending score update (Super Admin only)"""
    
    result = manual_update()
    return {
        "message": "Manual trending update completed",
        "details": result
    }

@app.get("/api/admin/tools/trending-stats")
async def get_trending_stats(
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Get trending statistics for admin dashboard"""
    
    tools = db.query(Tool).all()
    
    # Calculate statistics
    total_tools = len(tools)
    total_views = sum(tool.views for tool in tools)
    avg_trending_score = sum(tool.trending_score for tool in tools) / total_tools if total_tools > 0 else 0
    
    # Get top trending tools
    top_trending = db.query(Tool).order_by(desc(Tool.trending_score)).limit(5).all()
    
    return {
        "total_tools": total_tools,
        "total_views": total_views,
        "avg_trending_score": avg_trending_score,
        "top_trending": [
            {
                "name": tool.name,
                "trending_score": tool.trending_score,
                "views": tool.views,
                "rating": tool.rating
            }
            for tool in top_trending
        ]
    }

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

# Categories CRUD Routes
@app.get("/api/categories", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    categories = db.query(Category).all()
    return categories

@app.post("/api/categories", response_model=CategoryResponse)
async def create_category(
    category: CategoryCreate,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Create a new category"""
    db_category = Category(
        id=str(uuid.uuid4()),
        name=category.name,
        description=category.description,
        icon=category.icon,
        color=category.color,
        created_at=datetime.utcnow()
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

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
    """Generate SEO optimization for a tool (Admin only - must have access to tool)"""
    from auth import check_tool_access
    
    # Check if admin has access to this tool
    if not check_tool_access(current_user, request.tool_id, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this tool. Please request access from a superadmin."
        )
    
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
    """Get SEO optimizations for tools accessible to current admin"""
    
    if current_user.user_type == "superadmin":
        # Superadmins can see all optimizations
        optimizations = db.query(SEOOptimization).order_by(
            desc(SEOOptimization.created_at)
        ).offset(skip).limit(limit).all()
    else:
        # Regular admins only see optimizations for their assigned tools
        optimizations = db.query(SEOOptimization).join(Tool).filter(
            Tool.assigned_admin_id == current_user.id
        ).order_by(desc(SEOOptimization.created_at)).offset(skip).limit(limit).all()
    
    return optimizations

@app.get("/api/admin/seo/tools")
async def get_seo_tools(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get SEO status for tools accessible to current admin"""
    
    if current_user.user_type == "superadmin":
        # Superadmins can see all tools
        tools = db.query(Tool).all()
    else:
        # Regular admins only see assigned tools
        tools = db.query(Tool).filter(Tool.assigned_admin_id == current_user.id).all()
    
    seo_tools = []
    for tool in tools:
        seo_tools.append({
            "tool_id": tool.id,
            "tool_name": tool.name,
            "has_meta_title": bool(tool.ai_meta_title or tool.meta_title),
            "has_meta_description": bool(tool.ai_meta_description or tool.meta_description),
            "has_ai_content": bool(tool.ai_content),
            "optimizations_count": len(tool.seo_optimizations),
            "last_updated": tool.last_updated,
            "assigned_admin_id": tool.assigned_admin_id
        })
    
    return seo_tools

# Blog Routes
@app.get("/api/blogs", response_model=List[BlogResponse])
async def get_blogs(
    skip: int = 0,
    limit: int = 20,
    status: str = "published",
    category_id: Optional[str] = None,
    author_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    db: Session = Depends(get_db)
):
    query = db.query(Blog).filter(Blog.status == status)
    
    if category_id:
        query = query.filter(Blog.category_id == category_id)
    if author_id:
        query = query.filter(Blog.author_id == author_id)
    if search:
        query = query.filter(
            Blog.title.ilike(f"%{search}%") | 
            Blog.content.ilike(f"%{search}%")
        )
    
    # Sorting
    if sort_by == "views":
        query = query.order_by(desc(Blog.views))
    elif sort_by == "likes":
        query = query.order_by(desc(Blog.likes))
    elif sort_by == "oldest":
        query = query.order_by(asc(Blog.created_at))
    else:
        query = query.order_by(desc(Blog.created_at))
    
    blogs = query.offset(skip).limit(limit).all()
    return blogs

@app.get("/api/blogs/{blog_id}", response_model=BlogResponse)
async def get_blog(blog_id: str, db: Session = Depends(get_db)):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Increment view count
    blog.views += 1
    db.commit()
    
    return blog

@app.post("/api/blogs", response_model=BlogResponse)
async def create_blog(
    blog: BlogCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    # Calculate reading time (average 200 words per minute)
    word_count = len(blog.content.split())
    reading_time = max(1, round(word_count / 200))
    
    db_blog = Blog(
        id=str(uuid.uuid4()),
        author_id=current_user.id,
        reading_time=reading_time,
        published_at=datetime.utcnow() if blog.status == "published" else None,
        **blog.dict()
    )
    db.add(db_blog)
    db.commit()
    db.refresh(db_blog)
    return db_blog

@app.put("/api/blogs/{blog_id}", response_model=BlogResponse)
async def update_blog(
    blog_id: str,
    blog_update: BlogUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    db_blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not db_blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Check permissions
    if db_blog.author_id != current_user.id and current_user.user_type not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    update_data = blog_update.dict(exclude_unset=True)
    
    # Update reading time if content changed
    if 'content' in update_data:
        word_count = len(update_data['content'].split())
        update_data['reading_time'] = max(1, round(word_count / 200))
    
    # Set published_at if status changes to published
    if update_data.get('status') == 'published' and db_blog.status != 'published':
        update_data['published_at'] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(db_blog, field, value)
    
    db.commit()
    db.refresh(db_blog)
    return db_blog

@app.delete("/api/blogs/{blog_id}")
async def delete_blog(
    blog_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    db_blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not db_blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Check permissions
    if db_blog.author_id != current_user.id and current_user.user_type not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(db_blog)
    db.commit()
    return {"message": "Blog deleted successfully"}

@app.post("/api/blogs/{blog_id}/like")
async def like_blog(
    blog_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    blog.likes += 1
    db.commit()
    
    return {"likes": blog.likes}

# Category Management Routes
@app.put("/api/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    category_update: CategoryUpdate,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = category_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@app.delete("/api/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db.delete(db_category)
    db.commit()
    return {"message": "Category deleted successfully"}

# Subcategory Routes
@app.post("/api/subcategories", response_model=SubcategoryResponse)
async def create_subcategory(
    subcategory: SubcategoryCreate,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    db_subcategory = Subcategory(
        id=str(uuid.uuid4()),
        **subcategory.dict()
    )
    db.add(db_subcategory)
    db.commit()
    db.refresh(db_subcategory)
    return db_subcategory

# Super Admin User Management Routes
@app.get("/api/admin/users", response_model=List[UserResponse])
async def get_all_users(
    current_user: User = Depends(require_superadmin),
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    user_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all users with filtering (Super Admin only)"""
    query = db.query(User)
    
    if search:
        query = query.filter(
            User.full_name.ilike(f"%{search}%") |
            User.email.ilike(f"%{search}%") |
            User.username.ilike(f"%{search}%")
        )
    
    if user_type:
        query = query.filter(User.user_type == user_type)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    users = query.offset(skip).limit(limit).all()
    return users

@app.get("/api/admin/users/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Get user by ID (Super Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/api/admin/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Update user details (Super Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow changing own role
    if user.id == current_user.id and user_update.user_type is not None:
        raise HTTPException(
            status_code=400,
            detail="Cannot change your own role"
        )
    
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

@app.delete("/api/admin/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Delete user (Super Admin only)"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@app.post("/api/admin/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Create new user (Super Admin only)"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        id=str(uuid.uuid4()),
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        user_type=user_data.user_type,
        is_active=True,
        is_verified=True  # Admin created users are auto-verified
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Reviews Management Routes
@app.get("/api/admin/reviews", response_model=List[ReviewResponse])
async def get_all_reviews(
    current_user: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 100,
    tool_id: Optional[str] = None,
    is_verified: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all reviews (Admin only)"""
    query = db.query(Review)
    
    if tool_id:
        query = query.filter(Review.tool_id == tool_id)
    
    if is_verified is not None:
        query = query.filter(Review.is_verified == is_verified)
    
    reviews = query.order_by(desc(Review.created_at)).offset(skip).limit(limit).all()
    return reviews

@app.put("/api/admin/reviews/{review_id}/verify")
async def verify_review(
    review_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Verify a review (Admin only)"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    review.is_verified = True
    db.commit()
    return {"message": "Review verified successfully"}

@app.delete("/api/admin/reviews/{review_id}")
async def delete_review(
    review_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a review (Admin only)"""
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    db.delete(review)
    db.commit()
    return {"message": "Review deleted successfully"}

# Analytics and Dashboard for Super Admin
@app.get("/api/admin/analytics/advanced")
async def get_advanced_analytics(
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Get advanced analytics (Super Admin only)"""
    
    # User statistics
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    admin_users = db.query(User).filter(User.user_type.in_(["admin", "superadmin"])).count()
    
    # Content statistics
    total_tools = db.query(Tool).count()
    featured_tools = db.query(Tool).filter(Tool.is_featured == True).count()
    total_blogs = db.query(Blog).count()
    published_blogs = db.query(Blog).filter(Blog.status == "published").count()
    
    # Review statistics
    total_reviews = db.query(Review).count()
    verified_reviews = db.query(Review).filter(Review.is_verified == True).count()
    avg_rating = db.query(func.avg(Review.rating)).scalar() or 0
    
    # Recent activity
    recent_users = db.query(User).order_by(desc(User.created_at)).limit(10).all()
    recent_reviews = db.query(Review).order_by(desc(Review.created_at)).limit(10).all()
    
    return {
        "user_stats": {
            "total": total_users,
            "active": active_users,
            "verified": verified_users,
            "admins": admin_users
        },
        "content_stats": {
            "total_tools": total_tools,
            "featured_tools": featured_tools,
            "total_blogs": total_blogs,
            "published_blogs": published_blogs
        },
        "review_stats": {
            "total": total_reviews,
            "verified": verified_reviews,
            "average_rating": float(avg_rating)
        },
        "recent_activity": {
            "users": recent_users,
            "reviews": recent_reviews
        }
    }

# CSV Sample File Generation
@app.get("/api/admin/tools/sample-csv")
async def download_sample_csv(
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Download sample CSV file for bulk tool upload"""
    
    # Get sample categories for reference
    sample_categories = db.query(Category).limit(3).all()
    
    # Read the sample CSV file
    import os
    csv_file_path = os.path.join(os.path.dirname(__file__), "static", "tools_sample.csv")
    
    try:
        with open(csv_file_path, 'r') as file:
            csv_content = file.read()
        
        # Replace placeholder category IDs with actual ones
        if sample_categories:
            csv_content = csv_content.replace(
                "REPLACE_WITH_ACTUAL_CATEGORY_ID", 
                sample_categories[0].id
            )
        else:
            csv_content = csv_content.replace(
                "REPLACE_WITH_ACTUAL_CATEGORY_ID", 
                "CREATE_CATEGORIES_FIRST"
            )
        
        # Return as downloadable file
        from fastapi.responses import Response
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=tools_sample.csv",
                "Content-Type": "text/csv"
            }
        )
        
    except FileNotFoundError:
        # Fallback to programmatic generation
        sample_data = [
            {
                "name": "Example Tool 1",
                "description": "This is a comprehensive project management tool designed for teams",
                "short_description": "Project management made easy",
                "website_url": "https://example-tool1.com",
                "pricing_model": "Freemium",
                "pricing_details": "Free tier available, Pro starts at $10/month",
                "features": "Task management, Team collaboration, Time tracking, Reporting",
                "target_audience": "Small to medium businesses",
                "company_size": "SMB",
                "integrations": "Slack, Google Drive, Dropbox, GitHub",
                "logo_url": "https://example.com/logo1.png",
                "category_id": sample_categories[0].id if sample_categories else "CREATE_CATEGORIES_FIRST",
                "industry": "Technology",
                "employee_size": "11-50",
                "revenue_range": "1M-10M",
                "location": "San Francisco, CA",
                "is_hot": "true",
                "is_featured": "false",
                "meta_title": "Example Tool 1 - Project Management Solution",
                "meta_description": "Streamline your project management with Example Tool 1",
                "slug": "example-tool-1"
            }
        ]
        
        # Generate CSV content
        import io
        import csv
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=sample_data[0].keys())
        writer.writeheader()
        writer.writerows(sample_data)
        csv_content = output.getvalue()
        
        from fastapi.responses import Response
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=tools_sample.csv",
                "Content-Type": "text/csv"
            }
        )

# Role Management Routes
@app.post("/api/admin/users/{user_id}/promote")
async def promote_user_to_admin(
    user_id: str,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Promote user to admin (Super Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.user_type == "superadmin":
        raise HTTPException(
            status_code=400,
            detail="Cannot modify superadmin role"
        )
    
    user.user_type = "admin"
    db.commit()
    return {"message": f"User {user.username} promoted to admin"}

@app.post("/api/admin/users/{user_id}/demote")
async def demote_admin_to_user(
    user_id: str,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Demote admin to user (Super Admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.user_type == "superadmin":
        raise HTTPException(
            status_code=400,
            detail="Cannot demote superadmin"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Cannot demote yourself"
        )
    
    user.user_type = "user"
    db.commit()
    return {"message": f"Admin {user.username} demoted to user"}

# SEO Management Routes
@app.get("/api/admin/seo/tools")
async def get_seo_tools(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get SEO status for tools (Admin only)"""
    
    tools = db.query(Tool).all()
    seo_tools = []
    for tool in tools:
        seo_tools.append({
            "tool_id": tool.id,
            "tool_name": tool.name,
            "has_meta_title": bool(tool.ai_meta_title or tool.meta_title),
            "has_meta_description": bool(tool.ai_meta_description or tool.meta_description),
            "has_ai_content": bool(tool.ai_content),
            "optimizations_count": len(tool.seo_optimizations),
            "last_updated": tool.last_updated
        })
    
    return seo_tools

# Free Tools Routes (Public)
@app.get("/api/free-tools", response_model=List[FreeToolResponse])
async def get_free_tools(
    skip: int = 0,
    limit: int = 20,
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """Get all free tools (public endpoint)"""
    query = db.query(FreeTool).filter(FreeTool.is_active == is_active)
    
    if category:
        query = query.filter(FreeTool.category == category)
    
    if search:
        query = query.filter(
            FreeTool.name.ilike(f"%{search}%") | 
            FreeTool.description.ilike(f"%{search}%")
        )
    
    tools = query.offset(skip).limit(limit).all()
    return tools

@app.get("/api/free-tools/{tool_id}", response_model=FreeToolResponse)
async def get_free_tool(tool_id: str, db: Session = Depends(get_db)):
    """Get a specific free tool (public endpoint)"""
    tool = db.query(FreeTool).filter(FreeTool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Free tool not found")
    
    # Increment view count
    tool.views += 1
    db.commit()
    
    return tool

@app.get("/api/free-tools/slug/{slug}", response_model=FreeToolResponse)
async def get_free_tool_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a free tool by slug (public endpoint)"""
    tool = db.query(FreeTool).filter(FreeTool.slug == slug).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Free tool not found")
    
    # Increment view count
    tool.views += 1
    db.commit()
    
    return tool

# Helper function to get current user (optional)
def get_token_optional(authorization: str = Header(None)):
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None

def get_current_user_optional(token: str = Depends(get_token_optional)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except JWTError:
        return None
    
    db = next(get_db())
    user = get_user(db, username=token_data.username)
    if user is None:
        return None
    return user

# Search Routes (Public)
@app.post("/api/free-tools/{tool_id}/search", response_model=SearchResponse)
async def search_with_tool(
    tool_id: str,
    search_request: SearchRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Perform search using a free tool"""
    tool = db.query(FreeTool).filter(FreeTool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Free tool not found")
    
    # Perform search
    if search_request.engine == "google":
        search_result = await search_service.search_google(search_request.query, search_request.num_results)
    elif search_request.engine == "bing":
        search_result = await search_service.search_bing(search_request.query, search_request.num_results)
    else:
        raise HTTPException(status_code=400, detail="Invalid search engine")
    
    # Save search history
    search_history = SearchHistory(
        id=str(uuid.uuid4()),
        tool_id=tool_id,
        user_id=current_user.id if current_user else None,
        search_engine=search_request.engine,
        query=search_request.query,
        results_count=len(search_result.results),
        results=json.dumps([result.dict() for result in search_result.results]),
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", "")
    )
    
    db.add(search_history)
    
    # Update tool search count
    tool.searches_count += 1
    db.commit()
    
    # Add tool_id to response
    search_result.tool_id = tool_id
    
    return search_result

@app.post("/api/free-tools/{tool_id}/search/combined")
async def combined_search_with_tool(
    tool_id: str,
    search_request: SearchRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Perform combined search (Google + Bing) using a free tool"""
    tool = db.query(FreeTool).filter(FreeTool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Free tool not found")
    
    # Perform combined search
    combined_results = await search_service.combined_search(
        search_request.query, 
        ["google", "bing"], 
        search_request.num_results
    )
    
    # Save search history for both engines
    for engine in ["google", "bing"]:
        if engine in combined_results:
            search_result = combined_results[engine]
            search_history = SearchHistory(
                id=str(uuid.uuid4()),
                tool_id=tool_id,
                user_id=current_user.id if current_user else None,
                search_engine=engine,
                query=search_request.query,
                results_count=len(search_result.results),
                results=json.dumps([result.dict() for result in search_result.results]),
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent", "")
            )
            db.add(search_history)
    
    # Update tool search count
    tool.searches_count += 2  # Both Google and Bing
    db.commit()
    
    return combined_results

@app.get("/api/free-tools/{tool_id}/search-history", response_model=List[SearchHistoryResponse])
async def get_tool_search_history(
    tool_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get search history for a specific tool (Admin only)"""
    history = db.query(SearchHistory).filter(
        SearchHistory.tool_id == tool_id
    ).order_by(desc(SearchHistory.created_at)).offset(skip).limit(limit).all()
    
    return history

# Free Tools Admin Routes
@app.post("/api/admin/free-tools", response_model=FreeToolResponse)
async def create_free_tool(
    tool: FreeToolCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new free tool (Admin only)"""
    # Check if slug already exists
    existing_tool = db.query(FreeTool).filter(FreeTool.slug == tool.slug).first()
    if existing_tool:
        raise HTTPException(status_code=400, detail="Slug already exists")
    
    db_tool = FreeTool(
        id=str(uuid.uuid4()),
        **tool.dict()
    )
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    return db_tool

@app.put("/api/admin/free-tools/{tool_id}", response_model=FreeToolResponse)
async def update_free_tool(
    tool_id: str,
    tool_update: FreeToolUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a free tool (Admin only)"""
    db_tool = db.query(FreeTool).filter(FreeTool.id == tool_id).first()
    if not db_tool:
        raise HTTPException(status_code=404, detail="Free tool not found")
    
    update_data = tool_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_tool, field, value)
    
    db.commit()
    db.refresh(db_tool)
    return db_tool

@app.delete("/api/admin/free-tools/{tool_id}")
async def delete_free_tool(
    tool_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a free tool (Admin only)"""
    db_tool = db.query(FreeTool).filter(FreeTool.id == tool_id).first()
    if not db_tool:
        raise HTTPException(status_code=404, detail="Free tool not found")
    
    db.delete(db_tool)
    db.commit()
    return {"message": "Free tool deleted successfully"}

@app.get("/api/admin/free-tools", response_model=List[FreeToolResponse])
async def get_all_free_tools_admin(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all free tools including inactive ones (Admin only)"""
    tools = db.query(FreeTool).offset(skip).limit(limit).all()
    return tools

# Bulk Upload for Free Tools
@app.post("/api/admin/free-tools/bulk-upload")
async def bulk_upload_free_tools(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Bulk upload free tools via CSV (Admin only)"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    csv_data = content.decode('utf-8')
    
    # Parse CSV and create free tools
    reader = csv.DictReader(io.StringIO(csv_data))
    created_tools = []
    errors = []
    
    for row_num, row in enumerate(reader, start=2):
        try:
            tool_data = {
                'id': str(uuid.uuid4()),
                'name': row['name'],
                'description': row['description'],
                'short_description': row.get('short_description', ''),
                'slug': row['slug'],
                'category': row.get('category', ''),
                'icon': row.get('icon', ''),
                'color': row.get('color', ''),
                'website_url': row.get('website_url', ''),
                'features': row.get('features', ''),
                'is_active': row.get('is_active', 'true').lower() == 'true',
                'meta_title': row.get('meta_title', ''),
                'meta_description': row.get('meta_description', '')
            }
            
            db_tool = FreeTool(**tool_data)
            db.add(db_tool)
            created_tools.append(tool_data['name'])
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    if created_tools:
        db.commit()
    
    return {
        "tools_created": len(created_tools),
        "created_tools": created_tools,
        "errors": errors
    }

# Free Tools Analytics
@app.get("/api/admin/free-tools/analytics")
async def get_free_tools_analytics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get analytics for free tools (Admin only)"""
    total_tools = db.query(FreeTool).count()
    active_tools = db.query(FreeTool).filter(FreeTool.is_active == True).count()
    total_searches = db.query(SearchHistory).count()
    total_views = db.query(func.sum(FreeTool.views)).scalar() or 0
    
    # Most popular tools
    popular_tools = db.query(FreeTool).order_by(desc(FreeTool.searches_count)).limit(10).all()
    
    # Recent search activity
    recent_searches = db.query(SearchHistory).order_by(desc(SearchHistory.created_at)).limit(20).all()
    
    return {
        "total_tools": total_tools,
        "active_tools": active_tools,
        "total_searches": total_searches,
        "total_views": total_views,
        "popular_tools": popular_tools,
        "recent_searches": recent_searches
    }

# Review Routes
@app.post("/api/tools/{tool_id}/reviews", response_model=ReviewResponse)
async def create_review(
    tool_id: str,
    review: ReviewCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Create a review for a tool"""
    # Check if tool exists
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Check if user already reviewed this tool
    existing_review = db.query(Review).filter(
        Review.tool_id == tool_id,
        Review.user_id == current_user.id
    ).first()
    
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this tool")
    
    # Create review
    db_review = Review(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        tool_id=tool_id,
        rating=review.rating,
        title=review.title,
        content=review.content,
        pros=review.pros,
        cons=review.cons
    )
    
    db.add(db_review)
    
    # Update tool rating statistics
    reviews = db.query(Review).filter(Review.tool_id == tool_id).all()
    total_reviews = len(reviews) + 1  # Include the new review
    avg_rating = (sum(r.rating for r in reviews) + review.rating) / total_reviews
    
    tool.rating = avg_rating
    tool.total_reviews = total_reviews
    
    db.commit()
    db.refresh(db_review)
    
    return db_review

@app.get("/api/tools/{tool_id}/reviews", response_model=List[ReviewResponse])
async def get_tool_reviews(
    tool_id: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get reviews for a tool"""
    reviews = db.query(Review).filter(Review.tool_id == tool_id).offset(skip).limit(limit).all()
    return reviews

@app.put("/api/reviews/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: str,
    review_update: ReviewCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update a review"""
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check if user owns the review
    if db_review.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this review")
    
    # Update review
    db_review.rating = review_update.rating
    db_review.title = review_update.title
    db_review.content = review_update.content
    db_review.pros = review_update.pros
    db_review.cons = review_update.cons
    
    db.commit()
    db.refresh(db_review)
    
    return db_review

@app.delete("/api/reviews/{review_id}")
async def delete_review(
    review_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Delete a review"""
    db_review = db.query(Review).filter(Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check if user owns the review or is admin
    if db_review.user_id != current_user.id and current_user.user_type not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")
    
    db.delete(db_review)
    db.commit()
    
    return {"message": "Review deleted successfully"}

# Comment Routes
@app.post("/api/blogs/{blog_id}/comments", response_model=CommentResponse)
async def create_comment(
    blog_id: str,
    comment: CommentCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Create a comment on a blog"""
    # Check if blog exists
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Check if parent comment exists (for nested comments)
    if comment.parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == comment.parent_id).first()
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")
    
    # Create comment
    db_comment = Comment(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        blog_id=blog_id,
        content=comment.content,
        parent_id=comment.parent_id
    )
    
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    return db_comment

@app.get("/api/blogs/{blog_id}/comments", response_model=List[CommentResponse])
async def get_blog_comments(
    blog_id: str,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get comments for a blog"""
    comments = db.query(Comment).filter(
        Comment.blog_id == blog_id,
        Comment.is_approved == True
    ).offset(skip).limit(limit).all()
    return comments

@app.put("/api/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: str,
    comment_update: CommentCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update a comment"""
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user owns the comment
    if db_comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    
    # Update comment
    db_comment.content = comment_update.content
    
    db.commit()
    db.refresh(db_comment)
    
    return db_comment

@app.delete("/api/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Delete a comment"""
    db_comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user owns the comment or is admin
    if db_comment.user_id != current_user.id and current_user.user_type not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    db.delete(db_comment)
    db.commit()
    
    return {"message": "Comment deleted successfully"}

# Tool Access Request Routes
@app.post("/api/admin/tools/{tool_id}/request-access", response_model=ToolAccessRequestResponse)
async def request_tool_access(
    tool_id: str,
    request_data: ToolAccessRequestCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Request access to a tool (Admin only)"""
    from models import ToolAccessRequest
    
    # Check if tool exists
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Check if admin already has access
    if tool.assigned_admin_id == current_user.id:
        raise HTTPException(status_code=400, detail="You already have access to this tool")
    
    # Check if there's already a pending request
    existing_request = db.query(ToolAccessRequest).filter(
        ToolAccessRequest.tool_id == tool_id,
        ToolAccessRequest.admin_id == current_user.id,
        ToolAccessRequest.status == "pending"
    ).first()
    
    if existing_request:
        raise HTTPException(status_code=400, detail="You already have a pending request for this tool")
    
    # Create access request
    access_request = ToolAccessRequest(
        id=str(uuid.uuid4()),
        tool_id=tool_id,
        admin_id=current_user.id,
        request_message=request_data.request_message,
        status="pending"
    )
    
    db.add(access_request)
    db.commit()
    db.refresh(access_request)
    
    # Add additional fields for response
    response = ToolAccessRequestResponse(
        id=access_request.id,
        tool_id=access_request.tool_id,
        admin_id=access_request.admin_id,
        superadmin_id=access_request.superadmin_id,
        status=access_request.status,
        request_message=access_request.request_message,
        response_message=access_request.response_message,
        created_at=access_request.created_at,
        updated_at=access_request.updated_at,
        tool_name=tool.name,
        admin_name=current_user.full_name
    )
    
    return response

@app.get("/api/admin/tools/access-requests", response_model=List[ToolAccessRequestResponse])
async def get_tool_access_requests(
    current_user: User = Depends(require_superadmin),
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all tool access requests (Super Admin only)"""
    from models import ToolAccessRequest
    
    query = db.query(ToolAccessRequest)
    
    if status:
        query = query.filter(ToolAccessRequest.status == status)
    
    requests = query.order_by(desc(ToolAccessRequest.created_at)).offset(skip).limit(limit).all()
    
    # Add additional fields for response
    response_list = []
    for request in requests:
        tool = db.query(Tool).filter(Tool.id == request.tool_id).first()
        admin = db.query(User).filter(User.id == request.admin_id).first()
        superadmin = db.query(User).filter(User.id == request.superadmin_id).first() if request.superadmin_id else None
        
        response_item = ToolAccessRequestResponse(
            id=request.id,
            tool_id=request.tool_id,
            admin_id=request.admin_id,
            superadmin_id=request.superadmin_id,
            status=request.status,
            request_message=request.request_message,
            response_message=request.response_message,
            created_at=request.created_at,
            updated_at=request.updated_at,
            tool_name=tool.name if tool else "Unknown Tool",
            admin_name=admin.full_name if admin else "Unknown Admin",
            superadmin_name=superadmin.full_name if superadmin else None
        )
        response_list.append(response_item)
    
    return response_list

@app.get("/api/admin/tools/my-requests", response_model=List[ToolAccessRequestResponse])
async def get_my_tool_requests(
    current_user: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get current admin's tool access requests"""
    from models import ToolAccessRequest
    
    requests = db.query(ToolAccessRequest).filter(
        ToolAccessRequest.admin_id == current_user.id
    ).order_by(desc(ToolAccessRequest.created_at)).offset(skip).limit(limit).all()
    
    # Add additional fields for response
    response_list = []
    for request in requests:
        tool = db.query(Tool).filter(Tool.id == request.tool_id).first()
        superadmin = db.query(User).filter(User.id == request.superadmin_id).first() if request.superadmin_id else None
        
        response_item = ToolAccessRequestResponse(
            id=request.id,
            tool_id=request.tool_id,
            admin_id=request.admin_id,
            superadmin_id=request.superadmin_id,
            status=request.status,
            request_message=request.request_message,
            response_message=request.response_message,
            created_at=request.created_at,
            updated_at=request.updated_at,
            tool_name=tool.name if tool else "Unknown Tool",
            admin_name=current_user.full_name,
            superadmin_name=superadmin.full_name if superadmin else None
        )
        response_list.append(response_item)
    
    return response_list

@app.put("/api/admin/tools/access-requests/{request_id}", response_model=ToolAccessRequestResponse)
async def process_tool_access_request(
    request_id: str,
    update_data: ToolAccessRequestUpdate,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Process a tool access request (Super Admin only)"""
    from models import ToolAccessRequest
    
    access_request = db.query(ToolAccessRequest).filter(ToolAccessRequest.id == request_id).first()
    if not access_request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    if access_request.status != "pending":
        raise HTTPException(status_code=400, detail="Request has already been processed")
    
    # Update request
    access_request.status = update_data.status
    access_request.response_message = update_data.response_message
    access_request.superadmin_id = current_user.id
    
    # If approved, assign the tool to the admin
    if update_data.status == "approved":
        tool = db.query(Tool).filter(Tool.id == access_request.tool_id).first()
        if tool:
            tool.assigned_admin_id = access_request.admin_id
    
    db.commit()
    db.refresh(access_request)
    
    # Add additional fields for response
    tool = db.query(Tool).filter(Tool.id == access_request.tool_id).first()
    admin = db.query(User).filter(User.id == access_request.admin_id).first()
    
    response = ToolAccessRequestResponse(
        id=access_request.id,
        tool_id=access_request.tool_id,
        admin_id=access_request.admin_id,
        superadmin_id=access_request.superadmin_id,
        status=access_request.status,
        request_message=access_request.request_message,
        response_message=access_request.response_message,
        created_at=access_request.created_at,
        updated_at=access_request.updated_at,
        tool_name=tool.name if tool else "Unknown Tool",
        admin_name=admin.full_name if admin else "Unknown Admin",
        superadmin_name=current_user.full_name
    )
    
    return response

@app.get("/api/admin/tools/assigned", response_model=List[ToolResponse])
async def get_assigned_tools(
    current_user: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get tools assigned to current admin"""
    
    # Superadmins can see all tools
    if current_user.user_type == "superadmin":
        tools = db.query(Tool).offset(skip).limit(limit).all()
    else:
        # Regular admins only see assigned tools
        tools = db.query(Tool).filter(
            Tool.assigned_admin_id == current_user.id
        ).offset(skip).limit(limit).all()
    
    return tools

# File Upload Route
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_verified_user)
):
    """Upload file and return base64 encoded data"""
    try:
        # Check file size (max 10MB)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB")
        
        # Check file type
        allowed_types = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp',
            'video/mp4', 'video/avi', 'video/mov', 'video/wmv'
        ]
        
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        # Convert to base64
        import base64
        base64_content = base64.b64encode(content).decode('utf-8')
        
        # Create data URL
        data_url = f"data:{file.content_type};base64,{base64_content}"
        
        return {
            "file_url": data_url,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file_size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Tool CRUD Routes
@app.post("/api/tools", response_model=ToolResponse)
async def create_tool(
    tool: ToolCreate,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Create a new tool (Super Admin only)"""
    
    # Check if slug already exists
    existing_tool = db.query(Tool).filter(Tool.slug == tool.slug).first()
    if existing_tool:
        raise HTTPException(status_code=400, detail="Slug already exists")
    
    # Check if category exists
    category = db.query(Category).filter(Category.id == tool.category_id).first()
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")
    
    # Check if subcategory exists (if provided)
    if tool.subcategory_id:
        subcategory = db.query(Subcategory).filter(Subcategory.id == tool.subcategory_id).first()
        if not subcategory:
            raise HTTPException(status_code=400, detail="Subcategory not found")
    
    # Create tool
    db_tool = Tool(
        id=str(uuid.uuid4()),
        **tool.dict(),
        created_at=datetime.utcnow(),
        last_updated=datetime.utcnow()
    )
    
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    
    return db_tool

@app.get("/api/tools", response_model=List[ToolResponse])
async def get_tools(
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all tools with optional filtering"""
    
    query = db.query(Tool)
    
    if category_id:
        query = query.filter(Tool.category_id == category_id)
    
    if search:
        query = query.filter(
            Tool.name.ilike(f"%{search}%") | 
            Tool.description.ilike(f"%{search}%")
        )
    
    tools = query.offset(skip).limit(limit).all()
    return tools

@app.get("/api/tools/{tool_id}", response_model=ToolResponse)
async def get_tool(tool_id: str, db: Session = Depends(get_db)):
    """Get a specific tool by ID"""
    
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Increment view count and update trending score
    increment_view_and_update_trending(tool_id, db)
    
    return tool

@app.put("/api/tools/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: str,
    tool_update: ToolUpdate,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Update a tool (Super Admin only)"""
    
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Check if slug already exists (if being updated)
    if tool_update.slug and tool_update.slug != tool.slug:
        existing_tool = db.query(Tool).filter(Tool.slug == tool_update.slug).first()
        if existing_tool:
            raise HTTPException(status_code=400, detail="Slug already exists")
    
    # Update tool
    update_data = tool_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tool, field, value)
    
    tool.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(tool)
    
    return tool

@app.delete("/api/tools/{tool_id}")
async def delete_tool(
    tool_id: str,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Delete a tool (Super Admin only)"""
    
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    db.delete(tool)
    db.commit()
    
    return {"message": "Tool deleted successfully"}

# Bulk Upload Tools
@app.post("/api/admin/tools/bulk-upload")
async def bulk_upload_tools(
    file: UploadFile = File(...),
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Bulk upload tools via CSV (Super Admin only)"""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    csv_data = content.decode('utf-8')
    
    # Parse CSV and create tools
    reader = csv.DictReader(io.StringIO(csv_data))
    created_tools = []
    errors = []
    
    for row_num, row in enumerate(reader, start=2):
        try:
            # Check if required fields are present
            if not all(field in row for field in ['name', 'description', 'category_id', 'slug']):
                errors.append(f"Row {row_num}: Missing required fields (name, description, category_id, slug)")
                continue
            
            # Check if category exists
            category = db.query(Category).filter(Category.id == row['category_id']).first()
            if not category:
                errors.append(f"Row {row_num}: Category not found with ID {row['category_id']}")
                continue
            
            # Check if slug already exists
            existing_tool = db.query(Tool).filter(Tool.slug == row['slug']).first()
            if existing_tool:
                errors.append(f"Row {row_num}: Slug '{row['slug']}' already exists")
                continue
            
            # Convert string boolean values
            is_hot = row.get('is_hot', 'false').lower() == 'true'
            is_featured = row.get('is_featured', 'false').lower() == 'true'
            
            # Create tool data
            tool_data = {
                'id': str(uuid.uuid4()),
                'name': row['name'],
                'description': row['description'],
                'short_description': row.get('short_description', ''),
                'website_url': row.get('website_url', ''),
                'pricing_model': row.get('pricing_model', ''),
                'pricing_details': row.get('pricing_details', ''),
                'features': row.get('features', ''),
                'target_audience': row.get('target_audience', ''),
                'company_size': row.get('company_size', ''),
                'integrations': row.get('integrations', ''),
                'logo_url': row.get('logo_url', ''),
                'screenshots': row.get('screenshots', ''),
                'video_url': row.get('video_url', ''),
                'category_id': row['category_id'],
                'subcategory_id': row.get('subcategory_id') if row.get('subcategory_id') else None,
                'industry': row.get('industry', ''),
                'employee_size': row.get('employee_size', ''),
                'revenue_range': row.get('revenue_range', ''),
                'location': row.get('location', ''),
                'is_hot': is_hot,
                'is_featured': is_featured,
                'meta_title': row.get('meta_title', ''),
                'meta_description': row.get('meta_description', ''),
                'slug': row['slug'],
                'created_at': datetime.utcnow(),
                'last_updated': datetime.utcnow()
            }
            
            # Handle launch_date if provided
            if row.get('launch_date'):
                try:
                    tool_data['launch_date'] = datetime.strptime(row['launch_date'], '%Y-%m-%d')
                except ValueError:
                    errors.append(f"Row {row_num}: Invalid date format for launch_date (use YYYY-MM-DD)")
                    continue
            
            db_tool = Tool(**tool_data)
            db.add(db_tool)
            created_tools.append(tool_data['name'])
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    if created_tools:
        db.commit()
    
    return {
        "tools_created": len(created_tools),
        "created_tools": created_tools,
        "errors": errors
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)