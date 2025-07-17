from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from database import get_db
from models import *
from schemas import *
from auth import get_current_verified_user, get_current_user_optional
from search_service import search_service
from trending_calculator import get_trending_analytics, increment_view_and_update_trending
from typing import Optional, List
import uuid
import json
import math
from jose import JWTError, jwt

router = APIRouter(prefix="/api/tools", tags=["tools"])

# Enhanced Tools Routes with Advanced Filtering
@router.get("/analytics")
async def get_tools_analytics(
    recalculate: bool = False,
    db: Session = Depends(get_db)
):
    """Get tools analytics for landing page with optional recalculation"""
    
    # Always recalculate trending scores to ensure fresh data
    analytics = get_trending_analytics(db, recalculate=True)
    
    # Convert to the expected response format
    return ToolAnalytics(
        trending_tools=analytics["trending_tools"],
        top_rated_tools=analytics["top_rated_tools"],
        most_viewed_tools=analytics["most_viewed_tools"],
        newest_tools=analytics["newest_tools"],
        featured_tools=analytics["featured_tools"],
        hot_tools=analytics["hot_tools"]
    )

@router.get("/search")
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

@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool_by_id(
    tool_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific tool by ID"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Increment view count and update trending
    increment_view_and_update_trending(db, tool_id)
    
    return tool

@router.get("/slug/{slug}", response_model=ToolResponse)
async def get_tool_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get a tool by slug"""
    tool = db.query(Tool).filter(Tool.slug == slug).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Increment view count and update trending
    increment_view_and_update_trending(db, tool.id)
    
    return tool

# Review Routes
@router.post("/{tool_id}/reviews", response_model=ReviewResponse)
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
        raise HTTPException(
            status_code=400, 
            detail="You have already reviewed this tool. Use the edit option to update your review."
        )
    
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

@router.get("/{tool_id}/reviews", response_model=List[ReviewResponse])
async def get_tool_reviews(
    tool_id: str,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get reviews for a tool with user's review status"""
    reviews = db.query(Review).filter(Review.tool_id == tool_id).offset(skip).limit(limit).all()
    
    # Add user's review status to each review
    for review in reviews:
        if current_user and review.user_id == current_user.id:
            review.is_own_review = True
        else:
            review.is_own_review = False
    
    return reviews

@router.get("/{tool_id}/review-status")
async def get_tool_review_status(
    tool_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get user's review status for a tool"""
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    
    # Check if user has reviewed this tool
    user_review = db.query(Review).filter(
        Review.tool_id == tool_id,
        Review.user_id == current_user.id
    ).first()
    
    return {
        "has_reviewed": user_review is not None,
        "review_id": user_review.id if user_review else None,
        "user_rating": user_review.rating if user_review else None,
        "total_reviews": tool.total_reviews,
        "average_rating": tool.rating
    }

@router.put("/reviews/{review_id}", response_model=ReviewResponse)
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

@router.delete("/reviews/{review_id}")
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

# Categories Routes
@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: Session = Depends(get_db)):
    """Get all categories"""
    categories = db.query(Category).all()
    return categories

@router.get("/categories/analytics")
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

# Free Tools Routes (Public)
free_tools_router = APIRouter(prefix="/api/free-tools", tags=["free-tools"])

@free_tools_router.get("", response_model=List[FreeToolResponse])
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

@free_tools_router.get("/{tool_id}", response_model=FreeToolResponse)
async def get_free_tool(tool_id: str, db: Session = Depends(get_db)):
    """Get a specific free tool (public endpoint)"""
    tool = db.query(FreeTool).filter(FreeTool.id == tool_id).first()
    if not tool:
        raise HTTPException(status_code=404, detail="Free tool not found")
    
    # Increment view count
    tool.views += 1
    db.commit()
    
    return tool

@free_tools_router.get("/slug/{slug}", response_model=FreeToolResponse)
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

def get_current_user_optional_local(token: str = Depends(get_token_optional)):
    if not token:
        return None
    try:
        from auth import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        from schemas import TokenData
        token_data = TokenData(username=username)
    except JWTError:
        return None
    
    from auth import get_user
    db = next(get_db())
    user = get_user(db, username=token_data.username)
    if user is None:
        return None
    return user

# Search Routes (Public)
@free_tools_router.post("/{tool_id}/search", response_model=SearchResponse)
async def search_with_tool(
    tool_id: str,
    search_request: SearchRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional_local)
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

@free_tools_router.post("/{tool_id}/search/combined")
async def combined_search_with_tool(
    tool_id: str,
    search_request: SearchRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional_local)
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

# Include both routers
def get_tools_routes():
    """Return combined tools routes"""
    main_router = APIRouter()
    main_router.include_router(router)
    main_router.include_router(free_tools_router)
    return main_router