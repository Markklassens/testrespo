from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
from models import *
from schemas import *
from auth import require_superadmin, get_password_hash
from typing import Optional, List
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/superadmin", tags=["superadmin"])

# Admin Settings Management
@router.get("/settings")
async def get_admin_settings(
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Get all admin settings (Super Admin only)"""
    settings = db.query(AdminSettings).all()
    return {setting.setting_key: setting.setting_value for setting in settings}

@router.get("/settings/{setting_key}")
async def get_admin_setting(
    setting_key: str,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Get specific admin setting (Super Admin only)"""
    setting = db.query(AdminSettings).filter(AdminSettings.setting_key == setting_key).first()
    if not setting:
        return {"setting_key": setting_key, "setting_value": None}
    return {"setting_key": setting.setting_key, "setting_value": setting.setting_value}

@router.post("/settings/{setting_key}")
async def update_admin_setting(
    setting_key: str,
    setting_value: str,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Update admin setting (Super Admin only)"""
    setting = db.query(AdminSettings).filter(AdminSettings.setting_key == setting_key).first()
    
    if setting:
        setting.setting_value = setting_value
        setting.updated_at = datetime.utcnow()
    else:
        setting = AdminSettings(
            id=str(uuid.uuid4()),
            setting_key=setting_key,
            setting_value=setting_value,
            description=f"Admin setting for {setting_key}"
        )
        db.add(setting)
    
    db.commit()
    db.refresh(setting)
    
    return {"message": f"Setting {setting_key} updated successfully", "setting": setting}

@router.delete("/settings/{setting_key}")
async def delete_admin_setting(
    setting_key: str,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Delete admin setting (Super Admin only)"""
    setting = db.query(AdminSettings).filter(AdminSettings.setting_key == setting_key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    db.delete(setting)
    db.commit()
    
    return {"message": f"Setting {setting_key} deleted successfully"}

# User Management Routes
@router.get("/users", response_model=List[UserResponse])
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

@router.get("/users/{user_id}", response_model=UserResponse)
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

@router.put("/users/{user_id}", response_model=UserResponse)
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

@router.delete("/users/{user_id}")
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

@router.post("/users", response_model=UserResponse)
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

# Role Management Routes
@router.post("/users/{user_id}/promote")
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

@router.post("/users/{user_id}/demote")
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

# Advanced Analytics Routes
@router.get("/analytics/advanced")
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

# Tool Access Request Management
@router.get("/tools/access-requests", response_model=List[ToolAccessRequestResponse])
async def get_tool_access_requests(
    current_user: User = Depends(require_superadmin),
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all tool access requests (Super Admin only)"""
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

@router.put("/tools/access-requests/{request_id}")
async def update_tool_access_request(
    request_id: str,
    update_data: ToolAccessRequestUpdate,
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Update tool access request (Super Admin only)"""
    access_request = db.query(ToolAccessRequest).filter(ToolAccessRequest.id == request_id).first()
    if not access_request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    # Update request
    access_request.status = update_data.status
    access_request.response_message = update_data.response_message
    access_request.superadmin_id = current_user.id
    access_request.updated_at = datetime.utcnow()
    
    # If approved, assign tool to admin
    if update_data.status == "approved":
        tool = db.query(Tool).filter(Tool.id == access_request.tool_id).first()
        if tool:
            tool.assigned_admin_id = access_request.admin_id
    
    db.commit()
    return {"message": f"Access request {update_data.status} successfully"}

# Category Management Routes
@router.post("/categories", response_model=CategoryResponse)
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

@router.put("/categories/{category_id}", response_model=CategoryResponse)
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

@router.delete("/categories/{category_id}")
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
@router.post("/subcategories", response_model=SubcategoryResponse)
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

# Trending Management Routes
@router.post("/tools/update-trending")
async def update_tools_trending_scores(
    current_user: User = Depends(require_superadmin),
    db: Session = Depends(get_db)
):
    """Update trending scores for all tools (Super Admin only)"""
    from trending_calculator import update_trending_scores
    
    result = update_trending_scores(db)
    return {
        "message": "Trending scores updated successfully",
        "details": result
    }

@router.post("/tools/update-trending-manual")
async def manual_update_trending(
    current_user: User = Depends(require_superadmin)
):
    """Manually trigger trending score update (Super Admin only)"""
    from scheduler import manual_update
    
    result = manual_update()
    return {
        "message": "Manual trending update completed",
        "details": result
    }

@router.get("/tools/trending-stats")
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

# CSV Sample File Generation
@router.get("/tools/sample-csv")
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