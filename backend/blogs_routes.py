from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc
from database import get_db
from models import Blog, Comment, User, Category, user_blog_likes, BlogReview
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
    query = db.query(Blog)
    
    # If status is provided, filter by status, otherwise get all statuses
    if status != "all":
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
async def toggle_blog_like(
    blog_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Toggle like on a blog (like/unlike)"""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Check if user already liked this blog
    existing_like = db.query(user_blog_likes).filter(
        user_blog_likes.c.user_id == current_user.id,
        user_blog_likes.c.blog_id == blog_id
    ).first()
    
    if existing_like:
        # Unlike the blog
        db.execute(
            user_blog_likes.delete().where(
                user_blog_likes.c.user_id == current_user.id,
                user_blog_likes.c.blog_id == blog_id
            )
        )
        blog.likes = max(0, blog.likes - 1)
        action = "unliked"
    else:
        # Like the blog
        db.execute(
            user_blog_likes.insert().values(
                user_id=current_user.id,
                blog_id=blog_id
            )
        )
        blog.likes += 1
        action = "liked"
    
    db.commit()
    
    return {
        "action": action,
        "likes": blog.likes,
        "user_liked": action == "liked"
    }

@router.get("/{blog_id}/like-status")
async def get_blog_like_status(
    blog_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get user's like status for a blog"""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Check if user liked this blog
    user_liked = db.query(user_blog_likes).filter(
        user_blog_likes.c.user_id == current_user.id,
        user_blog_likes.c.blog_id == blog_id
    ).first() is not None
    
    return {
        "user_liked": user_liked,
        "total_likes": blog.likes
    }

# Blog Review Routes
@router.post("/{blog_id}/reviews", response_model=BlogReviewResponse)
async def create_blog_review(
    blog_id: str,
    review: BlogReviewCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Create a review for a blog"""
    # Check if blog exists
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Check if user already reviewed this blog
    existing_review = db.query(BlogReview).filter(
        BlogReview.blog_id == blog_id,
        BlogReview.user_id == current_user.id
    ).first()
    
    if existing_review:
        raise HTTPException(
            status_code=400, 
            detail="You have already reviewed this blog. Use the edit option to update your review."
        )
    
    # Create review
    db_review = BlogReview(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        blog_id=blog_id,
        rating=review.rating,
        title=review.title,
        content=review.content,
        pros=review.pros,
        cons=review.cons
    )
    
    db.add(db_review)
    
    # Update blog rating statistics
    reviews = db.query(BlogReview).filter(BlogReview.blog_id == blog_id).all()
    total_reviews = len(reviews) + 1  # Include the new review
    avg_rating = (sum(r.rating for r in reviews) + review.rating) / total_reviews
    
    blog.rating = avg_rating
    blog.total_reviews = total_reviews
    
    db.commit()
    db.refresh(db_review)
    
    return db_review

@router.get("/{blog_id}/reviews", response_model=List[BlogReviewResponse])
async def get_blog_reviews(
    blog_id: str,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Get reviews for a blog with user's review status"""
    from auth import get_current_user_optional
    
    reviews = db.query(BlogReview).filter(BlogReview.blog_id == blog_id).offset(skip).limit(limit).all()
    
    # Add user's review status to each review
    for review in reviews:
        if current_user and review.user_id == current_user.id:
            review.is_own_review = True
        else:
            review.is_own_review = False
    
    return reviews

@router.get("/{blog_id}/review-status")
async def get_blog_review_status(
    blog_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get user's review status for a blog"""
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")
    
    # Check if user has reviewed this blog
    user_review = db.query(BlogReview).filter(
        BlogReview.blog_id == blog_id,
        BlogReview.user_id == current_user.id
    ).first()
    
    return {
        "has_reviewed": user_review is not None,
        "review_id": user_review.id if user_review else None,
        "user_rating": user_review.rating if user_review else None,
        "total_reviews": blog.total_reviews,
        "average_rating": blog.rating
    }

@router.get("/{blog_id}/reviews/my-review", response_model=BlogReviewResponse)
async def get_my_blog_review(
    blog_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get current user's review for a blog"""
    review = db.query(BlogReview).filter(
        BlogReview.blog_id == blog_id,
        BlogReview.user_id == current_user.id
    ).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="You haven't reviewed this blog yet")
    
    return review

@router.put("/reviews/{review_id}", response_model=BlogReviewResponse)
async def update_blog_review(
    review_id: str,
    review_update: BlogReviewCreate,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Update a blog review"""
    db_review = db.query(BlogReview).filter(BlogReview.id == review_id).first()
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
    
    # Recalculate blog rating statistics
    blog = db.query(Blog).filter(Blog.id == db_review.blog_id).first()
    if blog:
        reviews = db.query(BlogReview).filter(BlogReview.blog_id == db_review.blog_id).all()
        if reviews:
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            blog.rating = avg_rating
            blog.total_reviews = len(reviews)
    
    db.commit()
    db.refresh(db_review)
    
    return db_review

@router.delete("/reviews/{review_id}")
async def delete_blog_review(
    review_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Delete a blog review"""
    db_review = db.query(BlogReview).filter(BlogReview.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Check if user owns the review or is admin
    if db_review.user_id != current_user.id and current_user.user_type not in ["admin", "superadmin"]:
        raise HTTPException(status_code=403, detail="Not authorized to delete this review")
    
    blog_id = db_review.blog_id
    db.delete(db_review)
    
    # Recalculate blog rating statistics
    blog = db.query(Blog).filter(Blog.id == blog_id).first()
    if blog:
        reviews = db.query(BlogReview).filter(BlogReview.blog_id == blog_id).all()
        if reviews:
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            blog.rating = avg_rating
            blog.total_reviews = len(reviews)
        else:
            blog.rating = 0.0
            blog.total_reviews = 0
    
    db.commit()
    
    return {"message": "Review deleted successfully"}

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