from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
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
    groq_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None

class UserResponse(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    groq_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    
    class Config:
        from_attributes = True

# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

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
    icon: Optional[str] = None
    color: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None

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
    icon: Optional[str] = None

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
    industry: Optional[str] = None
    employee_size: Optional[str] = None
    revenue_range: Optional[str] = None
    location: Optional[str] = None
    is_hot: bool = False
    is_featured: bool = False
    launch_date: Optional[datetime] = None
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
    industry: Optional[str] = None
    employee_size: Optional[str] = None
    revenue_range: Optional[str] = None
    location: Optional[str] = None
    is_hot: Optional[bool] = None
    is_featured: Optional[bool] = None
    launch_date: Optional[datetime] = None
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
    is_ai_generated: bool = False
    ai_prompt: Optional[str] = None

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
    is_ai_generated: bool
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# AI Content Generation Schemas
class AIContentRequest(BaseModel):
    prompt: str
    content_type: str  # blog, tool_description, seo_content
    provider: Optional[str] = None  # groq, claude, or auto
    model: Optional[str] = None

class AIContentResponse(BaseModel):
    content: str
    provider: str
    model: str
    tokens_used: int

# SEO Optimization Schemas
class SEOOptimizationRequest(BaseModel):
    tool_id: str
    target_keywords: List[str]
    search_engine: str  # google, bing
    provider: Optional[str] = None  # groq, claude, or auto

class SEOOptimizationResponse(BaseModel):
    meta_title: str
    meta_description: str
    content: str
    optimization_score: float
    keywords_used: List[str]

# Enhanced Search Schemas
class AdvancedSearchRequest(BaseModel):
    q: Optional[str] = None
    category_id: Optional[str] = None
    subcategory_id: Optional[str] = None
    pricing_model: Optional[str] = None
    company_size: Optional[str] = None
    industry: Optional[str] = None
    employee_size: Optional[str] = None
    revenue_range: Optional[str] = None
    location: Optional[str] = None
    is_hot: Optional[bool] = None
    is_featured: Optional[bool] = None
    min_rating: Optional[float] = None
    sort_by: Optional[str] = "relevance"
    skip: int = 0
    limit: int = 20

class PaginatedToolsResponse(BaseModel):
    tools: List[ToolResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

# Analytics Schemas
class ToolAnalytics(BaseModel):
    trending_tools: List[ToolResponse]
    top_rated_tools: List[ToolResponse]
    most_viewed_tools: List[ToolResponse]
    newest_tools: List[ToolResponse]
    featured_tools: List[ToolResponse]
    hot_tools: List[ToolResponse]

class CategoryAnalytics(BaseModel):
    category_id: str
    category_name: str
    tool_count: int
    avg_rating: float
    total_views: int
    recommended_tools: List[ToolResponse]

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
    is_own_review: Optional[bool] = False
    
    class Config:
        from_attributes = True

class ReviewStatusResponse(BaseModel):
    has_reviewed: bool
    review_id: Optional[str] = None
    user_rating: Optional[int] = None
    total_reviews: int
    average_rating: float

class BlogLikeResponse(BaseModel):
    action: str
    likes: int
    user_liked: bool

class BlogLikeStatusResponse(BaseModel):
    user_liked: bool
    total_likes: int

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

# Admin Settings Schemas
class AdminSettingBase(BaseModel):
    setting_key: str
    setting_value: Optional[str] = None
    description: Optional[str] = None

class AdminSettingCreate(AdminSettingBase):
    pass

class AdminSettingResponse(AdminSettingBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# File Upload Response
class FileUploadResponse(BaseModel):
    file_url: str
    filename: str
    content_type: str
    size: int

# Tool Comparison Schema
class ToolComparisonRequest(BaseModel):
    tool_id: str

# Analytics Response
class AnalyticsResponse(BaseModel):
    total_users: int
    total_tools: int
    total_blogs: int
    total_reviews: int
    recent_blogs: List[BlogResponse]
    recent_reviews: List[ReviewResponse]

# Advanced Analytics Schema
class AdvancedAnalyticsResponse(BaseModel):
    user_stats: Dict[str, int]
    content_stats: Dict[str, int]  
    review_stats: Dict[str, Any]
    recent_activity: Dict[str, Any]

# SEO Tool Status Schema
class SEOToolStatus(BaseModel):
    tool_id: str
    tool_name: str
    has_meta_title: bool
    has_meta_description: bool
    has_ai_content: bool
    optimizations_count: int
    last_updated: datetime

# Role Management Schemas
class RoleUpdateRequest(BaseModel):
    user_id: str
    new_role: str

class RoleUpdateResponse(BaseModel):
    message: str
    user_id: str
    old_role: str
    new_role: str

# Free Tool Schemas
class FreeToolBase(BaseModel):
    name: str
    description: str
    short_description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    website_url: Optional[str] = None
    features: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: str

class FreeToolCreate(FreeToolBase):
    pass

class FreeToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    website_url: Optional[str] = None
    features: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None

class FreeToolResponse(FreeToolBase):
    id: str
    views: int
    searches_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Search Schemas
class SearchRequest(BaseModel):
    query: str
    engine: str  # google, bing
    num_results: int = 10

class SearchResult(BaseModel):
    title: str
    link: str
    snippet: str
    displayLink: Optional[str] = None

class SearchResponse(BaseModel):
    engine: str
    query: str
    results: List[SearchResult]
    total_results: Optional[int] = None
    tool_id: Optional[str] = None

class SearchHistoryResponse(BaseModel):
    id: str
    tool_id: str
    user_id: Optional[str] = None
    search_engine: str
    query: str
    results_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Tool Assignment Schema
class ToolAssignmentRequest(BaseModel):
    admin_id: str

class ToolAssignmentResponse(BaseModel):
    message: str
    tool_id: str
    tool_name: str
    admin_id: str
    admin_name: str

# Combined Search Response
class CombinedSearchResponse(BaseModel):
    google: Optional[SearchResponse] = None
    bing: Optional[SearchResponse] = None
    errors: Dict[str, str] = {}

# Tool Access Request Schemas
class ToolAccessRequestBase(BaseModel):
    tool_id: str
    request_message: Optional[str] = None

class ToolAccessRequestCreate(ToolAccessRequestBase):
    pass

class ToolAccessRequestUpdate(BaseModel):
    status: str  # approved, denied
    response_message: Optional[str] = None

class ToolAccessRequestResponse(BaseModel):
    id: str
    tool_id: str
    admin_id: str
    superadmin_id: Optional[str] = None
    status: str
    request_message: Optional[str] = None
    response_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Additional fields for display
    tool_name: Optional[str] = None
    admin_name: Optional[str] = None
    superadmin_name: Optional[str] = None
    
    class Config:
        from_attributes = True

# API Keys Management Schemas
class APIKeysUpdate(BaseModel):
    groq_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None

class APIKeysResponse(BaseModel):
    groq_api_key: Optional[str] = None
    claude_api_key: Optional[str] = None
    groq_configured: bool = False
    claude_configured: bool = False