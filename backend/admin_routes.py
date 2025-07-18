from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc
from database import get_db
from models import *
from schemas import *
from auth import require_admin, require_superadmin, check_tool_access
from ai_services import ai_manager
from typing import Optional, List
import uuid
import json
import csv
import io
from datetime import datetime

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Tool Content Management Routes
@router.put("/tools/{tool_id}/content", response_model=ToolResponse)
async def update_tool_content(
    tool_id: str,
    content_update: ToolUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update tool content (Admin only - must have access to tool)"""
    
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

@router.post("/tools/{tool_id}/request-access", response_model=ToolAccessRequestResponse)
async def request_tool_access(
    tool_id: str,
    request_data: ToolAccessRequestCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Request access to a tool (Admin only)"""
    
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

@router.get("/tools/my-requests", response_model=List[ToolAccessRequestResponse])
async def get_my_tool_requests(
    current_user: User = Depends(require_admin),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get current admin's tool access requests"""
    
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

# Review Management Routes
@router.get("/reviews", response_model=List[ReviewResponse])
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

@router.put("/reviews/{review_id}/verify")
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

@router.delete("/reviews/{review_id}")
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

# Free Tools Admin Management Routes
@router.post("/free-tools", response_model=FreeToolResponse)
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

@router.put("/free-tools/{tool_id}", response_model=FreeToolResponse)
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

@router.delete("/free-tools/{tool_id}")
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

@router.get("/free-tools", response_model=List[FreeToolResponse])
async def get_all_free_tools_admin(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all free tools including inactive ones (Admin only)"""
    tools = db.query(FreeTool).offset(skip).limit(limit).all()
    return tools

@router.post("/free-tools/bulk-upload")
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

@router.get("/free-tools/analytics")
async def get_free_tools_analytics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get analytics for free tools (Admin only)"""
    from sqlalchemy import func
    
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

@router.get("/free-tools/{tool_id}/search-history", response_model=List[SearchHistoryResponse])
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

# SEO Management Routes
@router.post("/seo/optimize")
async def optimize_tool_seo(
    request: SEOOptimizationRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Generate SEO optimization for a tool (Admin only - must have access to tool)"""
    
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

@router.get("/seo/optimizations")
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

@router.get("/seo/tools")
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

# Free Tools Admin Routes
@router.post("/free-tools", response_model=FreeToolResponse)
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

@router.put("/free-tools/{tool_id}", response_model=FreeToolResponse)
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

@router.delete("/free-tools/{tool_id}")
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

@router.get("/free-tools", response_model=List[FreeToolResponse])
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
@router.post("/free-tools/bulk-upload")
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
@router.get("/free-tools/analytics")
async def get_free_tools_analytics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get analytics for free tools (Admin only)"""
    from sqlalchemy import func
    
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

@router.get("/free-tools/{tool_id}/search-history", response_model=List[SearchHistoryResponse])
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