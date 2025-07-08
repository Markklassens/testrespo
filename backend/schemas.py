from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    user_type: str = "user"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    user_type: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

class EmailVerification(BaseModel):
    token: str

# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Subcategory Schemas
class SubcategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: str

class SubcategoryCreate(SubcategoryBase):
    pass

class SubcategoryResponse(SubcategoryBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Tool Schemas
class ToolBase(BaseModel):
    name: str
    description: str
    short_description: Optional[str] = None
    website_url: Optional[str] = None
    pricing_model: Optional[str] = None
    pricing_details: Optional[str] = None
    features: Optional[str] = None
    target_audience: Optional[str] = None
    company_size: Optional[str] = None
    integrations: Optional[str] = None
    logo_url: Optional[str] = None
    screenshots: Optional[str] = None
    video_url: Optional[str] = None
    category_id: str
    subcategory_id: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: str

class ToolCreate(ToolBase):
    pass

class ToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    website_url: Optional[str] = None
    pricing_model: Optional[str] = None
    pricing_details: Optional[str] = None
    features: Optional[str] = None
    target_audience: Optional[str] = None
    company_size: Optional[str] = None
    integrations: Optional[str] = None
    logo_url: Optional[str] = None
    screenshots: Optional[str] = None
    video_url: Optional[str] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

class ToolResponse(ToolBase):
    id: str
    rating: float
    total_reviews: int
    views: int
    trending_score: float
    last_updated: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# Blog Schemas
class BlogBase(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    status: str = "draft"
    featured_image: Optional[str] = None
    category_id: str
    subcategory_id: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: str

class BlogCreate(BlogBase):
    pass

class BlogUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    status: Optional[str] = None
    featured_image: Optional[str] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

class BlogResponse(BlogBase):
    id: str
    author_id: str
    views: int
    likes: int
    reading_time: int
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Review Schemas
class ReviewBase(BaseModel):
    rating: int
    title: str
    content: str
    pros: Optional[str] = None
    cons: Optional[str] = None
    tool_id: str

class ReviewCreate(ReviewBase):
    pass

class ReviewResponse(ReviewBase):
    id: str
    user_id: str
    is_verified: bool
    helpful_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Enhanced Search Response
class SearchResponse(BaseModel):
    tools: List[ToolResponse]
    total: int
    skip: int
    limit: int

# File Upload Response
class FileUploadResponse(BaseModel):
    file_url: str
    filename: str

# Analytics Response
class AnalyticsResponse(BaseModel):
    total_users: int
    total_tools: int
    total_blogs: int
    total_reviews: int
    recent_blogs: List[BlogResponse]
    recent_reviews: List[ReviewResponse]

# Review Schemas
class ReviewBase(BaseModel):
    rating: int
    title: str
    content: str
    pros: Optional[str] = None
    cons: Optional[str] = None
    tool_id: str

class ReviewCreate(ReviewBase):
    pass

class ReviewResponse(ReviewBase):
    id: str
    user_id: str
    is_verified: bool
    helpful_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Comment Schemas
class CommentBase(BaseModel):
    content: str
    blog_id: str
    parent_id: Optional[str] = None

class CommentCreate(CommentBase):
    pass

class CommentResponse(CommentBase):
    id: str
    user_id: str
    is_approved: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True