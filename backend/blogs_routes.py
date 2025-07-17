from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from database import get_db
from models import Blog, Comment, User, Category
from schemas import *
from auth import get_current_verified_user
from typing import Optional, List
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/blogs", tags=["blogs"])

@router.get("", response_model=List[BlogResponse])
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
    """Get blogs with filtering and sorting"""
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

@router.get("/{blog_id}", response_model=BlogResponse)
async def get_blog(blog_id: str, db: Session = Depends(get_db)):
    """Get a specific blog by ID"""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Increment view count
    blog.views += 1
    db.commit()
    
    return blog

@router.get("/slug/{slug}", response_model=BlogResponse)
async def get_blog_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a blog by slug"""
    blog = db.query(Blog).filter(Blog.slug == slug).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Increment view count
    blog.views += 1
    db.commit()
    
    return blog

@router.post("", response_model=BlogResponse)
async def create_blog(
    blog: BlogCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Create a new blog"""
    # Check if slug already exists
    existing_blog = db.query(Blog).filter(Blog.slug == blog.slug).first()
    if existing_blog:
        raise HTTPException(status_code=400, detail="Slug already exists")
    
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

@router.put("/{blog_id}", response_model=BlogResponse)
async def update_blog(
    blog_id: str,
    blog_update: BlogUpdate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update a blog"""
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

@router.delete("/{blog_id}")
async def delete_blog(
    blog_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Delete a blog"""
    db_blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not db_blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Check permissions
    if db_blog.author_id != current_user.id and current_user.user_type not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    db.delete(db_blog)
    db.commit()
    return {"message": "Blog deleted successfully"}

@router.post("/{blog_id}/like")
async def like_blog(
    blog_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Like a blog"""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    blog.likes += 1
    db.commit()
    
    return {"likes": blog.likes}

# Comment Routes
@router.post("/{blog_id}/comments", response_model=CommentResponse)
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

@router.get("/{blog_id}/comments", response_model=List[CommentResponse])
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

@router.put("/comments/{comment_id}", response_model=CommentResponse)
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

@router.delete("/comments/{comment_id}")
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

# Blog Analytics Routes
@router.get("/analytics/stats")
async def get_blog_analytics(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get blog analytics statistics"""
    
    # Overall blog statistics
    total_blogs = db.query(Blog).count()
    published_blogs = db.query(Blog).filter(Blog.status == "published").count()
    draft_blogs = db.query(Blog).filter(Blog.status == "draft").count()
    
    # User's blog statistics (if not admin)
    if current_user.user_type not in ["admin", "superadmin"]:
        user_blogs = db.query(Blog).filter(Blog.author_id == current_user.id).count()
        user_published = db.query(Blog).filter(
            Blog.author_id == current_user.id,
            Blog.status == "published"
        ).count()
        user_drafts = db.query(Blog).filter(
            Blog.author_id == current_user.id,
            Blog.status == "draft"
        ).count()
    else:
        user_blogs = total_blogs
        user_published = published_blogs
        user_drafts = draft_blogs
    
    # Most viewed blogs
    most_viewed = db.query(Blog).order_by(desc(Blog.views)).limit(10).all()
    
    # Most liked blogs
    most_liked = db.query(Blog).order_by(desc(Blog.likes)).limit(10).all()
    
    # Recent blogs
    recent_blogs = db.query(Blog).order_by(desc(Blog.created_at)).limit(10).all()
    
    return {
        "total_stats": {
            "total_blogs": total_blogs,
            "published_blogs": published_blogs,
            "draft_blogs": draft_blogs
        },
        "user_stats": {
            "user_blogs": user_blogs,
            "user_published": user_published,
            "user_drafts": user_drafts
        },
        "popular_content": {
            "most_viewed": most_viewed,
            "most_liked": most_liked,
            "recent_blogs": recent_blogs
        }
    }

@router.get("/categories/stats")
async def get_blog_category_stats(db: Session = Depends(get_db)):
    """Get blog statistics by category"""
    
    categories = db.query(Category).all()
    category_stats = []
    
    for category in categories:
        blog_count = db.query(Blog).filter(
            Blog.category_id == category.id,
            Blog.status == "published"
        ).count()
        
        if blog_count > 0:
            total_views = db.query(Blog).filter(
                Blog.category_id == category.id,
                Blog.status == "published"
            ).with_entities(func.sum(Blog.views)).scalar() or 0
            
            total_likes = db.query(Blog).filter(
                Blog.category_id == category.id,
                Blog.status == "published"
            ).with_entities(func.sum(Blog.likes)).scalar() or 0
            
            avg_views = total_views / blog_count if blog_count > 0 else 0
            avg_likes = total_likes / blog_count if blog_count > 0 else 0
        else:
            total_views = 0
            total_likes = 0
            avg_views = 0
            avg_likes = 0
        
        category_stats.append({
            "category_id": category.id,
            "category_name": category.name,
            "blog_count": blog_count,
            "total_views": total_views,
            "total_likes": total_likes,
            "avg_views": avg_views,
            "avg_likes": avg_likes
        })
    
    return category_stats

# Author performance routes
@router.get("/authors/stats")
async def get_author_stats(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get author performance statistics"""
    
    # Only admins can see all authors, regular users see only their own stats
    if current_user.user_type in ["admin", "superadmin"]:
        # Get top authors by blog count
        from sqlalchemy import func
        author_stats = db.query(
            User.id,
            User.full_name,
            func.count(Blog.id).label('blog_count'),
            func.sum(Blog.views).label('total_views'),
            func.sum(Blog.likes).label('total_likes')
        ).join(Blog).filter(
            Blog.status == "published"
        ).group_by(User.id, User.full_name).order_by(
            desc(func.count(Blog.id))
        ).limit(20).all()
        
        return {
            "top_authors": [
                {
                    "author_id": stat.id,
                    "author_name": stat.full_name,
                    "blog_count": stat.blog_count,
                    "total_views": stat.total_views or 0,
                    "total_likes": stat.total_likes or 0
                }
                for stat in author_stats
            ]
        }
    else:
        # Return current user's stats only
        user_blogs = db.query(Blog).filter(
            Blog.author_id == current_user.id,
            Blog.status == "published"
        ).all()
        
        total_views = sum(blog.views for blog in user_blogs)
        total_likes = sum(blog.likes for blog in user_blogs)
        
        return {
            "user_stats": {
                "author_id": current_user.id,
                "author_name": current_user.full_name,
                "blog_count": len(user_blogs),
                "total_views": total_views,
                "total_likes": total_likes,
                "avg_views": total_views / len(user_blogs) if user_blogs else 0,
                "avg_likes": total_likes / len(user_blogs) if user_blogs else 0
            }
        }

@router.get("/trending")
async def get_trending_blogs(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get trending blogs based on recent activity"""
    from datetime import datetime, timedelta
    
    # Get blogs from last 30 days sorted by views + likes
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    trending_blogs = db.query(Blog).filter(
        Blog.status == "published",
        Blog.created_at >= thirty_days_ago
    ).order_by(
        desc(Blog.views + Blog.likes)
    ).limit(limit).all()
    
    return trending_blogs