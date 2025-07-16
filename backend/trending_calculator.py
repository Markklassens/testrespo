"""
Trending Score Calculator

This module calculates trending scores for tools based on multiple factors:
- Recent views (time-weighted)
- Rating and number of reviews
- Recency of tool (newer tools get slight boost)
- Current hot/featured status
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from models import Tool

def calculate_trending_score(tool: Tool, avg_views: float, avg_rating: float, avg_reviews: float) -> float:
    """
    Calculate trending score for a tool based on multiple factors.
    
    Args:
        tool: The tool object
        avg_views: Average views across all tools
        avg_rating: Average rating across all tools
        avg_reviews: Average number of reviews across all tools
    
    Returns:
        Float trending score between 0-100
    """
    
    # Base score from views (normalized to 40 points max)
    views_score = min(40.0, (tool.views / max(avg_views, 1)) * 20)
    
    # Rating score (normalized to 25 points max)
    rating_score = (tool.rating / 5.0) * 25.0
    
    # Reviews count score (normalized to 15 points max)
    reviews_score = min(15.0, (tool.total_reviews / max(avg_reviews, 1)) * 7.5)
    
    # Recency boost (newer tools get up to 10 points)
    # Handle timezone-aware datetime comparison
    now = datetime.utcnow()
    if tool.created_at.tzinfo is not None:
        # If tool.created_at has timezone info, make now aware
        from datetime import timezone
        now = now.replace(tzinfo=timezone.utc)
    
    days_old = (now - tool.created_at).days
    if days_old < 30:
        recency_score = 10.0 * (1 - (days_old / 30))
    elif days_old < 90:
        recency_score = 5.0 * (1 - ((days_old - 30) / 60))
    else:
        recency_score = 0.0
    
    # Hot/Featured boost (5 points each)
    hot_bonus = 5.0 if tool.is_hot else 0.0
    featured_bonus = 5.0 if tool.is_featured else 0.0
    
    # Calculate final score
    trending_score = views_score + rating_score + reviews_score + recency_score + hot_bonus + featured_bonus
    
    # Ensure score is between 0 and 100
    return min(100.0, max(0.0, trending_score))

def update_trending_scores(db: Session) -> Dict[str, Any]:
    """
    Update trending scores for all tools in the database.
    
    Args:
        db: Database session
    
    Returns:
        Dictionary with update statistics
    """
    
    # Get all tools
    tools = db.query(Tool).all()
    
    if not tools:
        return {
            "total_tools": 0,
            "updated_tools": 0,
            "error": "No tools found"
        }
    
    # Calculate averages for normalization
    total_views = sum(tool.views for tool in tools)
    total_rating = sum(tool.rating for tool in tools if tool.rating > 0)
    total_reviews = sum(tool.total_reviews for tool in tools)
    
    avg_views = total_views / len(tools)
    avg_rating = total_rating / len([tool for tool in tools if tool.rating > 0]) if any(tool.rating > 0 for tool in tools) else 0
    avg_reviews = total_reviews / len(tools)
    
    # Update trending scores for each tool
    updated_count = 0
    score_changes = []
    
    for tool in tools:
        old_score = tool.trending_score
        new_score = calculate_trending_score(tool, avg_views, avg_rating, avg_reviews)
        
        tool.trending_score = new_score
        tool.last_updated = datetime.utcnow().replace(tzinfo=None).replace(tzinfo=None)
        
        score_changes.append({
            "tool_name": tool.name,
            "old_score": old_score,
            "new_score": new_score,
            "change": new_score - old_score
        })
        
        updated_count += 1
    
    # Commit changes
    db.commit()
    
    return {
        "total_tools": len(tools),
        "updated_tools": updated_count,
        "averages": {
            "views": avg_views,
            "rating": avg_rating,
            "reviews": avg_reviews
        },
        "score_changes": score_changes
    }

def get_trending_analytics(db: Session, recalculate: bool = False) -> Dict[str, Any]:
    """
    Get trending analytics, optionally recalculating scores first.
    
    Args:
        db: Database session
        recalculate: Whether to recalculate trending scores before returning data
    
    Returns:
        Dictionary with trending analytics
    """
    
    if recalculate:
        update_result = update_trending_scores(db)
    else:
        update_result = None
    
    # Get trending tools
    trending_tools = db.query(Tool).order_by(desc(Tool.trending_score)).limit(10).all()
    
    # Get top rated tools
    top_rated_tools = db.query(Tool).filter(Tool.total_reviews > 0).order_by(desc(Tool.rating)).limit(10).all()
    
    # Get most viewed tools
    most_viewed_tools = db.query(Tool).order_by(desc(Tool.views)).limit(10).all()
    
    # Get newest tools (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    newest_tools = db.query(Tool).filter(Tool.created_at >= thirty_days_ago).order_by(desc(Tool.created_at)).limit(10).all()
    
    # Get featured tools
    featured_tools = db.query(Tool).filter(Tool.is_featured == True).limit(10).all()
    
    # Get hot tools
    hot_tools = db.query(Tool).filter(Tool.is_hot == True).limit(10).all()
    
    return {
        "trending_tools": trending_tools,
        "top_rated_tools": top_rated_tools,
        "most_viewed_tools": most_viewed_tools,
        "newest_tools": newest_tools,
        "featured_tools": featured_tools,
        "hot_tools": hot_tools,
        "update_result": update_result
    }

def increment_view_and_update_trending(db: Session, tool_id: str) -> Tool:
    """
    Increment a tool's view count and update its trending score.
    
    Args:
        db: Database session
        tool_id: ID of the tool to update
    
    Returns:
        Updated tool object
    """
    
    tool = db.query(Tool).filter(Tool.id == tool_id).first()
    if not tool:
        return None
    
    # Increment view count
    tool.views += 1
    
    # Get current averages for trending calculation
    tools = db.query(Tool).all()
    if tools:
        avg_views = sum(t.views for t in tools) / len(tools)
        avg_rating = sum(t.rating for t in tools if t.rating > 0) / len([t for t in tools if t.rating > 0]) if any(t.rating > 0 for t in tools) else 0
        avg_reviews = sum(t.total_reviews for t in tools) / len(tools)
        
        # Update trending score
        tool.trending_score = calculate_trending_score(tool, avg_views, avg_rating, avg_reviews)
    
    tool.last_updated = datetime.utcnow().replace(tzinfo=None)
    db.commit()
    
    return tool