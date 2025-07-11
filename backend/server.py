from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Query, Request, Header
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
from backend.search_service import search_service
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

# Tools Routes
@app.get("/api/tools", response_model=List[ToolResponse])
async def get_tools(
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Tool)
    if category_id:
        query = query.filter(Tool.category_id == category_id)
    tools = query.offset(skip).limit(limit).all()
    return tools

@app.get("/api/tools/{tool_id}", response_model=ToolResponse)
async def get_tool(tool_id: str, db: Session = Depends(get_db)):
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Increment view count
    tool.views += 1
    db.commit()
    
    return tool

@app.post("/api/tools", response_model=ToolResponse)
async def create_tool(
    tool: ToolCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    db_tool = Tool(
        id=str(uuid.uuid4()),
        **tool.dict()
    )
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    return db_tool

@app.put("/api/tools/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: str,
    tool_update: ToolUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    db_tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not db_tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    for field, value in tool_update.dict(exclude_unset=True).items():
        setattr(db_tool, field, value)
    
    db.commit()
    db.refresh(db_tool)
    return db_tool

@app.delete("/api/tools/{tool_id}")
async def delete_tool(
    tool_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    db_tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not db_tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    db.delete(db_tool)
    db.commit()
    return {"message": "Tool deleted successfully"}

# Tool Comparison Routes
@app.get("/api/tools/compare")
async def get_comparison_tools(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    # Direct query to get tools from the association table
    comparison_records = db.execute(
        text("SELECT tool_id FROM user_tool_comparison WHERE user_id = :user_id"),
        {"user_id": current_user.id}
    ).fetchall()
    
    if not comparison_records:
        return []
    
    tool_ids = [record[0] for record in comparison_records]
    tools = db.query(Tool).filter(Tool.id.in_(tool_ids)).all()
    
    return tools

@app.post("/api/tools/compare")
async def add_to_comparison(
    request: ToolComparisonRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    tool_id = request.tool_id
    
    # Check if tool exists
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Check if already in comparison
    existing = db.execute(
        user_tool_comparison.select().where(
            user_tool_comparison.c.user_id == current_user.id,
            user_tool_comparison.c.tool_id == tool_id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Tool already in comparison")
    
    # Add to comparison
    db.execute(
        user_tool_comparison.insert().values(
            user_id=current_user.id,
            tool_id=tool_id
        )
    )
    db.commit()
    
    return {"message": "Tool added to comparison"}

@app.delete("/api/tools/compare/{tool_id}")
async def remove_from_comparison(
    tool_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    db.execute(
        user_tool_comparison.delete().where(
            user_tool_comparison.c.user_id == current_user.id,
            user_tool_comparison.c.tool_id == tool_id
        )
    )
    db.commit()
    
    return {"message": "Tool removed from comparison"}

# Bulk Upload Routes
@app.post("/api/tools/bulk-upload")
async def bulk_upload_tools(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
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
            tool_data = {
                'id': str(uuid.uuid4()),
                'name': row['name'],
                'description': row['description'],
                'category_id': row['category_id'],
                'slug': row['name'].lower().replace(' ', '-'),
                **{k: v for k, v in row.items() if k not in ['name', 'description', 'category_id'] and v}
            }
            
            db_tool = Tool(**tool_data)
            db.add(db_tool)
            created_tools.append(tool_data['name'])
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    if created_tools:
        db.commit()
    
    return {
        "created_count": len(created_tools),
        "created_tools": created_tools,
        "errors": errors
    }

@app.get("/api/tools/csv-template")
async def get_csv_template():
    template_data = [
        {
            'name': 'Example Tool',
            'description': 'Example description',
            'category_id': 'category-uuid',
            'pricing_model': 'Freemium',
            'company_size': 'SMB',
            'website_url': 'https://example.com'
        }
    ]
    
    return {"template": template_data}

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
    current_user: User = Depends(require_admin),
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
    current_user: User = Depends(require_admin),
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
    current_user: User = Depends(require_admin),
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
    current_user: User = Depends(require_admin),
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
async def get_tools_seo_status(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get SEO status for all tools"""
    tools = db.query(Tool).all()
    seo_data = []
    
    for tool in tools:
        optimizations = db.query(SEOOptimization).filter(SEOOptimization.tool_id == tool.id).count()
        seo_data.append({
            "tool_id": tool.id,
            "tool_name": tool.name,
            "has_meta_title": bool(tool.meta_title),
            "has_meta_description": bool(tool.meta_description),
            "has_ai_content": bool(tool.ai_content),
            "optimizations_count": optimizations,
            "last_updated": tool.last_updated
        })
    
    return seo_data

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
        "created_count": len(created_tools),
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)