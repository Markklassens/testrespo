from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Blog, User
from schemas import *
from auth import get_current_verified_user
from groq_service import groq_service
from typing import Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import json
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-blog", tags=["ai-blog"])

# AI Content Generation Endpoints

@router.post("/generate-content")
async def generate_blog_content(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Generate blog content using AI"""
    try:
        # Extract parameters from request
        prompt = request.get('prompt', '')
        content_type = request.get('content_type', 'full_post')
        existing_content = request.get('existing_content', '')
        title = request.get('title', '')
        category = request.get('category', '')
        tone = request.get('tone', 'professional')
        length = request.get('length', 'medium')
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Generate content using Groq
        result = await groq_service.generate_blog_content(
            prompt=prompt,
            content_type=content_type,
            existing_content=existing_content,
            title=title,
            category=category,
            tone=tone,
            length=length
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=f"AI generation failed: {result.get('error', 'Unknown error')}")
        
        # Log AI usage for analytics
        logger.info(f"AI content generated for user {current_user.id}: {content_type}, {result['word_count']} words")
        
        return {
            "success": True,
            "content": result['content'],
            "word_count": result['word_count'],
            "reading_time": result['reading_time'],
            "content_type": content_type,
            "model_used": result.get('model_used', 'llama3-8b-8192')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_blog_content: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during content generation")

@router.post("/generate-titles")
async def generate_blog_titles(
    request: Dict[str, str],
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Generate blog title suggestions"""
    try:
        topic = request.get('topic', '')
        category = request.get('category', '')
        
        if not topic:
            raise HTTPException(status_code=400, detail="Topic is required")
        
        result = await groq_service.generate_blog_title(topic=topic, category=category)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=f"Title generation failed: {result.get('error', 'Unknown error')}")
        
        return {
            "success": True,
            "titles": result['titles']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_blog_titles: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during title generation")

@router.post("/improve-content")
async def improve_blog_content(
    request: Dict[str, str],
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Improve existing blog content using AI"""
    try:
        content = request.get('content', '')
        improvement_type = request.get('improvement_type', 'enhance')
        
        if not content:
            raise HTTPException(status_code=400, detail="Content is required")
        
        result = await groq_service.improve_content(
            content=content,
            improvement_type=improvement_type
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=f"Content improvement failed: {result.get('error', 'Unknown error')}")
        
        return {
            "success": True,
            "content": result['content'],
            "improvement_type": improvement_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in improve_blog_content: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during content improvement")

# Auto-save Draft Endpoints

@router.post("/auto-save-draft")
async def auto_save_draft(
    draft_data: Dict[str, Any],
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Auto-save blog draft to database"""
    try:
        # Extract draft data
        draft_id = draft_data.get('draft_id')
        title = draft_data.get('title', '')
        content = draft_data.get('content', '')
        category_id = draft_data.get('category_id')
        meta_data = draft_data.get('meta_data', {})
        
        # Create draft ID if not provided
        if not draft_id:
            draft_id = f"draft_{current_user.id}_{int(datetime.utcnow().timestamp())}"
        
        # Check if draft already exists
        existing_draft = db.query(Blog).filter(
            Blog.slug == draft_id,
            Blog.author_id == current_user.id,
            Blog.status == 'auto_draft'
        ).first()
        
        if existing_draft:
            # Update existing draft
            existing_draft.title = title
            existing_draft.content = content
            existing_draft.category_id = category_id
            existing_draft.meta_title = meta_data.get('meta_title', title)
            existing_draft.meta_description = meta_data.get('meta_description', '')
            existing_draft.updated_at = datetime.utcnow()
            
            # Calculate reading time
            word_count = len(content.split()) if content else 0
            existing_draft.reading_time = max(1, round(word_count / 200))
            
            db.commit()
            db.refresh(existing_draft)
            
            return {
                "success": True,
                "draft_id": draft_id,
                "message": "Draft updated successfully",
                "last_saved": existing_draft.updated_at.isoformat()
            }
        else:
            # Create new draft
            word_count = len(content.split()) if content else 0
            reading_time = max(1, round(word_count / 200))
            
            new_draft = Blog(
                id=str(uuid.uuid4()),
                title=title or "Untitled Draft",
                content=content,
                slug=draft_id,
                author_id=current_user.id,
                category_id=category_id,
                status='auto_draft',
                reading_time=reading_time,
                meta_title=meta_data.get('meta_title', title),
                meta_description=meta_data.get('meta_description', ''),
                excerpt='',
                views=0,
                likes=0
            )
            
            db.add(new_draft)
            db.commit()
            db.refresh(new_draft)
            
            return {
                "success": True,
                "draft_id": draft_id,
                "blog_id": new_draft.id,
                "message": "Draft saved successfully",
                "last_saved": new_draft.created_at.isoformat()
            }
            
    except Exception as e:
        logger.error(f"Error in auto_save_draft: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save draft")

@router.get("/drafts")
async def get_user_drafts(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get user's auto-saved drafts"""
    try:
        drafts = db.query(Blog).filter(
            Blog.author_id == current_user.id,
            Blog.status.in_(['draft', 'auto_draft'])
        ).order_by(Blog.updated_at.desc()).limit(10).all()
        
        draft_list = []
        for draft in drafts:
            draft_list.append({
                "id": draft.id,
                "draft_id": draft.slug if draft.status == 'auto_draft' else None,
                "title": draft.title,
                "content": draft.content,
                "category_id": draft.category_id,
                "status": draft.status,
                "created_at": draft.created_at.isoformat() if draft.created_at else None,
                "updated_at": draft.updated_at.isoformat() if draft.updated_at else None,
                "word_count": len(draft.content.split()) if draft.content else 0,
                "reading_time": draft.reading_time
            })
        
        return {
            "success": True,
            "drafts": draft_list
        }
        
    except Exception as e:
        logger.error(f"Error in get_user_drafts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve drafts")

@router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Delete a specific draft"""
    try:
        draft = db.query(Blog).filter(
            Blog.id == draft_id,
            Blog.author_id == current_user.id,
            Blog.status.in_(['draft', 'auto_draft'])
        ).first()
        
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        db.delete(draft)
        db.commit()
        
        return {
            "success": True,
            "message": "Draft deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_draft: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete draft")

# Blog Conversion and Publishing

@router.post("/publish-draft/{draft_id}")
async def publish_draft(
    draft_id: str,
    publish_data: Dict[str, Any],
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Convert draft to published blog"""
    try:
        draft = db.query(Blog).filter(
            Blog.id == draft_id,
            Blog.author_id == current_user.id,
            Blog.status.in_(['draft', 'auto_draft'])
        ).first()
        
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        # Update draft with publish data
        draft.title = publish_data.get('title', draft.title)
        draft.content = publish_data.get('content', draft.content)
        draft.category_id = publish_data.get('category_id', draft.category_id)
        draft.excerpt = publish_data.get('excerpt', '')
        draft.meta_title = publish_data.get('meta_title', draft.title)
        draft.meta_description = publish_data.get('meta_description', '')
        draft.status = 'published'
        draft.published_at = datetime.utcnow()
        
        # Generate proper slug if it was an auto-draft
        if draft.slug.startswith('draft_'):
            new_slug = publish_data.get('slug')
            if not new_slug:
                new_slug = re.sub(r'[^a-z0-9-]', '', draft.title.lower().replace(' ', '-'))
            draft.slug = new_slug
        
        # Update reading time
        word_count = len(draft.content.split()) if draft.content else 0
        draft.reading_time = max(1, round(word_count / 200))
        
        db.commit()
        db.refresh(draft)
        
        return {
            "success": True,
            "blog_id": draft.id,
            "message": "Draft published successfully",
            "published_at": draft.published_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in publish_draft: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to publish draft")

# AI Service Status

@router.get("/ai-status")
async def get_ai_service_status(
    current_user: User = Depends(get_current_verified_user)
):
    """Get AI service availability status"""
    return {
        "ai_available": groq_service.is_available(),
        "model": "llama3-8b-8192",
        "provider": "Groq",
        "features": [
            "full_post_generation",
            "content_continuation", 
            "section_generation",
            "title_suggestions",
            "content_improvement"
        ]
    }