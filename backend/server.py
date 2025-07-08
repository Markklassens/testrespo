from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from backend.database import get_db, engine
from backend.models import Base, User, Category, Subcategory, Tool, Blog, Review, Comment
from backend.schemas import *
from backend.auth import *
from backend.email_service import send_verification_email, send_password_reset_email, send_welcome_email
import uuid
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import csv
import io
import json
from typing import List, Optional

load_dotenv()

app = FastAPI(
    title="MarketMindAI API",
    description="B2B Blogging and Tools Platform",
    version="1.0.0"
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
    return {"status": "healthy", "app": "MarketMindAI"}

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

# User Management Routes (Admin/SuperAdmin only)
@app.get("/api/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Only superadmin can change user_type
    if user_update.user_type and current_user.user_type != "superadmin":
        raise HTTPException(
            status_code=403,
            detail="Only superadmin can change user type"
        )
    
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user

@app.delete("/api/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

# Category Routes
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
        description=category.description
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@app.put("/api/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    category: CategoryCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db_category.name = category.name
    db_category.description = category.description
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
@app.get("/api/subcategories", response_model=List[SubcategoryResponse])
async def get_subcategories(category_id: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Subcategory)
    if category_id:
        query = query.filter(Subcategory.category_id == category_id)
    subcategories = query.all()
    return subcategories

@app.post("/api/subcategories", response_model=SubcategoryResponse)
async def create_subcategory(
    subcategory: SubcategoryCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    db_subcategory = Subcategory(
        id=str(uuid.uuid4()),
        name=subcategory.name,
        description=subcategory.description,
        category_id=subcategory.category_id
    )
    db.add(db_subcategory)
    db.commit()
    db.refresh(db_subcategory)
    return db_subcategory

# Tool Routes
@app.get("/api/tools", response_model=List[ToolResponse])
async def get_tools(
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[str] = None,
    subcategory_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    db: Session = Depends(get_db)
):
    query = db.query(Tool)
    
    if category_id:
        query = query.filter(Tool.category_id == category_id)
    if subcategory_id:
        query = query.filter(Tool.subcategory_id == subcategory_id)
    if search:
        query = query.filter(Tool.name.ilike(f"%{search}%"))
    
    # Sorting
    if sort_by == "rating":
        query = query.order_by(Tool.rating.desc())
    elif sort_by == "trending":
        query = query.order_by(Tool.trending_score.desc())
    elif sort_by == "views":
        query = query.order_by(Tool.views.desc())
    else:
        query = query.order_by(Tool.created_at.desc())
    
    tools = query.offset(skip).limit(limit).all()
    return tools

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

@app.get("/api/tools/{tool_id}", response_model=ToolResponse)
async def get_tool(tool_id: str, db: Session = Depends(get_db)):
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Increment views
    tool.views += 1
    db.commit()
    return tool

# Tool Management Routes (Advanced)
@app.put("/api/tools/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: str,
    tool_update: ToolUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    for field, value in tool_update.dict(exclude_unset=True).items():
        setattr(tool, field, value)
    
    db.commit()
    db.refresh(tool)
    return tool

@app.delete("/api/tools/{tool_id}")
async def delete_tool(
    tool_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    db.delete(tool)
    db.commit()
    return {"message": "Tool deleted successfully"}

# Bulk CSV Upload for Tools
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
    csv_reader = csv.DictReader(io.StringIO(csv_data))
    
    tools_created = 0
    errors = []
    
    for row_num, row in enumerate(csv_reader, start=2):
        try:
            # Validate required fields
            if not all(row.get(field) for field in ['name', 'description', 'category_id', 'slug']):
                errors.append(f"Row {row_num}: Missing required fields")
                continue
            
            # Check if tool already exists
            if db.query(Tool).filter(Tool.slug == row['slug']).first():
                errors.append(f"Row {row_num}: Tool with slug '{row['slug']}' already exists")
                continue
            
            # Create tool
            tool = Tool(
                id=str(uuid.uuid4()),
                name=row['name'],
                description=row['description'],
                short_description=row.get('short_description', ''),
                website_url=row.get('website_url', ''),
                pricing_model=row.get('pricing_model', ''),
                pricing_details=row.get('pricing_details', ''),
                features=row.get('features', ''),
                target_audience=row.get('target_audience', ''),
                company_size=row.get('company_size', ''),
                integrations=row.get('integrations', ''),
                logo_url=row.get('logo_url', ''),
                category_id=row['category_id'],
                subcategory_id=row.get('subcategory_id', ''),
                slug=row['slug'],
                meta_title=row.get('meta_title', ''),
                meta_description=row.get('meta_description', '')
            )
            
            db.add(tool)
            tools_created += 1
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    try:
        db.commit()
        return {
            "message": f"Successfully uploaded {tools_created} tools",
            "tools_created": tools_created,
            "errors": errors
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

# CSV Template Download
@app.get("/api/tools/csv-template")
async def download_csv_template():
    template_data = [
        {
            "name": "Example Tool",
            "description": "This is an example tool description",
            "short_description": "Short description",
            "website_url": "https://example.com",
            "pricing_model": "Freemium",
            "pricing_details": "Free plan available, paid plans start at $10/month",
            "features": "Feature 1, Feature 2, Feature 3",
            "target_audience": "Small Business",
            "company_size": "SMB",
            "integrations": "Slack, Gmail, Zapier",
            "logo_url": "https://example.com/logo.png",
            "category_id": "your-category-id",
            "subcategory_id": "your-subcategory-id",
            "slug": "example-tool",
            "meta_title": "Example Tool - Best Tool for Your Business",
            "meta_description": "Discover Example Tool, the best solution for your business needs."
        }
    ]
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=template_data[0].keys())
    writer.writeheader()
    writer.writerows(template_data)
    
    return JSONResponse(
        content={"csv_content": output.getvalue()},
        headers={"Content-Disposition": "attachment; filename=tools_template.csv"}
    )

# Tool Comparison Routes
@app.post("/api/tools/compare")
async def add_tool_to_comparison(
    tool_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    # Check if tool exists
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Check if user already has this tool in comparison
    if tool in current_user.compared_tools:
        raise HTTPException(status_code=400, detail="Tool already in comparison")
    
    # Check if user already has 5 tools in comparison
    if len(current_user.compared_tools) >= 5:
        raise HTTPException(status_code=400, detail="Maximum 5 tools allowed in comparison")
    
    current_user.compared_tools.append(tool)
    db.commit()
    
    return {"message": "Tool added to comparison"}

@app.delete("/api/tools/compare/{tool_id}")
async def remove_tool_from_comparison(
    tool_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    if tool not in current_user.compared_tools:
        raise HTTPException(status_code=400, detail="Tool not in comparison")
    
    current_user.compared_tools.remove(tool)
    db.commit()
    
    return {"message": "Tool removed from comparison"}

@app.get("/api/tools/compare", response_model=List[ToolResponse])
async def get_comparison_tools(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    return current_user.compared_tools

# Advanced Tool Search and Filtering
@app.get("/api/tools/search")
async def search_tools(
    q: Optional[str] = None,
    category_id: Optional[str] = None,
    subcategory_id: Optional[str] = None,
    pricing_model: Optional[str] = None,
    company_size: Optional[str] = None,
    min_rating: Optional[float] = None,
    sort_by: Optional[str] = "relevance",
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(Tool)
    
    # Text search
    if q:
        query = query.filter(
            Tool.name.ilike(f"%{q}%") | 
            Tool.description.ilike(f"%{q}%") |
            Tool.features.ilike(f"%{q}%")
        )
    
    # Filters
    if category_id:
        query = query.filter(Tool.category_id == category_id)
    if subcategory_id:
        query = query.filter(Tool.subcategory_id == subcategory_id)
    if pricing_model:
        query = query.filter(Tool.pricing_model == pricing_model)
    if company_size:
        query = query.filter(Tool.company_size == company_size)
    if min_rating:
        query = query.filter(Tool.rating >= min_rating)
    
    # Sorting
    if sort_by == "rating":
        query = query.order_by(Tool.rating.desc())
    elif sort_by == "trending":
        query = query.order_by(Tool.trending_score.desc())
    elif sort_by == "views":
        query = query.order_by(Tool.views.desc())
    elif sort_by == "newest":
        query = query.order_by(Tool.created_at.desc())
    elif sort_by == "oldest":
        query = query.order_by(Tool.created_at.asc())
    else:  # relevance
        query = query.order_by(Tool.trending_score.desc())
    
    tools = query.offset(skip).limit(limit).all()
    total = query.count()
    
    return {
        "tools": tools,
        "total": total,
        "skip": skip,
        "limit": limit
    }

# Blog Routes (Enhanced)
@app.get("/api/blogs", response_model=List[BlogResponse])
async def get_blogs(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = "published",
    category_id: Optional[str] = None,
    author_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = "created_at",
    db: Session = Depends(get_db)
):
    query = db.query(Blog)
    
    if status:
        query = query.filter(Blog.status == status)
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
        query = query.order_by(Blog.views.desc())
    elif sort_by == "likes":
        query = query.order_by(Blog.likes.desc())
    elif sort_by == "oldest":
        query = query.order_by(Blog.created_at.asc())
    else:  # created_at
        query = query.order_by(Blog.created_at.desc())
    
    blogs = query.offset(skip).limit(limit).all()
    return blogs

@app.post("/api/blogs", response_model=BlogResponse)
async def create_blog(
    blog: BlogCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    # Calculate reading time (approximate)
    word_count = len(blog.content.split())
    reading_time = max(1, word_count // 200)  # Assuming 200 words per minute
    
    db_blog = Blog(
        id=str(uuid.uuid4()),
        author_id=current_user.id,
        reading_time=reading_time,
        **blog.dict()
    )
    
    if blog.status == "published":
        db_blog.published_at = datetime.utcnow()
    
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
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Check if user is the author or admin
    if blog.author_id != current_user.id and current_user.user_type not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to update this blog")
    
    for field, value in blog_update.dict(exclude_unset=True).items():
        setattr(blog, field, value)
    
    # Update reading time if content changed
    if blog_update.content:
        word_count = len(blog_update.content.split())
        blog.reading_time = max(1, word_count // 200)
    
    # Set published_at if status changed to published
    if blog_update.status == "published" and blog.published_at is None:
        blog.published_at = datetime.utcnow()
    
    db.commit()
    db.refresh(blog)
    return blog

@app.delete("/api/blogs/{blog_id}")
async def delete_blog(
    blog_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Check if user is the author or admin
    if blog.author_id != current_user.id and current_user.user_type not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this blog")
    
    db.delete(blog)
    db.commit()
    return {"message": "Blog deleted successfully"}

@app.get("/api/blogs/{blog_id}", response_model=BlogResponse)
async def get_blog(blog_id: str, db: Session = Depends(get_db)):
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Increment views
    blog.views += 1
    db.commit()
    return blog

# Blog Like/Unlike
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
    
    return {"message": "Blog liked", "likes": blog.likes}

# Reviews Routes
@app.post("/api/reviews", response_model=ReviewResponse)
async def create_review(
    review: ReviewCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    # Check if user already reviewed this tool
    existing_review = db.query(Review).filter(
        Review.user_id == current_user.id,
        Review.tool_id == review.tool_id
    ).first()
    
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this tool")
    
    db_review = Review(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        **review.dict()
    )
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Update tool rating
    tool = db.query(Tool).filter(Tool.id == review.tool_id).first()
    if tool:
        reviews = db.query(Review).filter(Review.tool_id == review.tool_id).all()
        tool.rating = sum(r.rating for r in reviews) / len(reviews)
        tool.total_reviews = len(reviews)
        db.commit()
    
    return db_review

@app.get("/api/reviews", response_model=List[ReviewResponse])
async def get_reviews(
    tool_id: Optional[str] = None,
    user_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    query = db.query(Review)
    
    if tool_id:
        query = query.filter(Review.tool_id == tool_id)
    if user_id:
        query = query.filter(Review.user_id == user_id)
    
    reviews = query.order_by(Review.created_at.desc()).offset(skip).limit(limit).all()
    return reviews

# Comments Routes
@app.post("/api/comments", response_model=CommentResponse)
async def create_comment(
    comment: CommentCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    db_comment = Comment(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        **comment.dict()
    )
    
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@app.get("/api/comments", response_model=List[CommentResponse])
async def get_comments(
    blog_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Comment).filter(Comment.is_approved == True)
    
    if blog_id:
        query = query.filter(Comment.blog_id == blog_id)
    
    comments = query.order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()
    return comments

# File Upload Routes
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_verified_user)
):
    # Create uploads directory if it doesn't exist
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Return file URL
    file_url = f"/api/static/{unique_filename}"
    return {"file_url": file_url, "filename": unique_filename}

# Serve static files
from fastapi.staticfiles import StaticFiles
uploads_dir = "/app/backend/uploads"
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/api/static", StaticFiles(directory=uploads_dir), name="static")

# Analytics Routes
@app.get("/api/analytics/dashboard")
async def get_dashboard_analytics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()
    total_tools = db.query(Tool).count()
    total_blogs = db.query(Blog).count()
    total_reviews = db.query(Review).count()
    
    # Get recent activity
    recent_blogs = db.query(Blog).order_by(Blog.created_at.desc()).limit(5).all()
    recent_reviews = db.query(Review).order_by(Review.created_at.desc()).limit(5).all()
    
    return {
        "total_users": total_users,
        "total_tools": total_tools,
        "total_blogs": total_blogs,
        "total_reviews": total_reviews,
        "recent_blogs": recent_blogs,
        "recent_reviews": recent_reviews
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)