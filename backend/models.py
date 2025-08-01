from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, Float, Table, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

# Association table for user-tool comparison
user_tool_comparison = Table(
    'user_tool_comparison',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('tool_id', String, ForeignKey('tools.id'), primary_key=True)
)

# Association table for user-blog likes
user_blog_likes = Table(
    'user_blog_likes',
    Base.metadata,
    Column('user_id', String, ForeignKey('users.id'), primary_key=True),
    Column('blog_id', String, ForeignKey('blogs.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    user_type = Column(String, default="user")  # user, admin, superadmin
    verification_token = Column(String, nullable=True)
    reset_token = Column(String, nullable=True)
    
    # AI API Keys for content generation
    groq_api_key = Column(String, nullable=True)
    claude_api_key = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    blogs = relationship("Blog", back_populates="author")
    reviews = relationship("Review", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    compared_tools = relationship("Tool", secondary=user_tool_comparison, back_populates="compared_by_users")
    ai_generated_content = relationship("AIGeneratedContent", back_populates="user")
    liked_blogs = relationship("Blog", secondary=user_blog_likes, back_populates="liked_by_users")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)  # Icon for UI
    color = Column(String, nullable=True)  # Color theme for category
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subcategories = relationship("Subcategory", back_populates="category")
    tools = relationship("Tool", back_populates="category")
    blogs = relationship("Blog", back_populates="category")

class Subcategory(Base):
    __tablename__ = "subcategories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    icon = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    category = relationship("Category", back_populates="subcategories")
    tools = relationship("Tool", back_populates="subcategory")
    blogs = relationship("Blog", back_populates="subcategory")

class Tool(Base):
    __tablename__ = "tools"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    short_description = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    pricing_model = Column(String, nullable=True)  # Free, Freemium, Paid
    pricing_details = Column(Text, nullable=True)
    features = Column(Text, nullable=True)  # JSON string
    target_audience = Column(String, nullable=True)
    company_size = Column(String, nullable=True)  # Startup, SMB, Enterprise
    integrations = Column(Text, nullable=True)  # JSON string
    logo_url = Column(String, nullable=True)
    screenshots = Column(Text, nullable=True)  # JSON string
    video_url = Column(String, nullable=True)
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    views = Column(Integer, default=0)
    trending_score = Column(Float, default=0.0)
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    subcategory_id = Column(String, ForeignKey("subcategories.id"), nullable=True)
    
    # Enhanced fields for advanced filtering
    industry = Column(String, nullable=True)  # Technology, Finance, Healthcare, etc.
    employee_size = Column(String, nullable=True)  # 1-10, 11-50, 51-200, 201-1000, 1000+
    revenue_range = Column(String, nullable=True)  # <1M, 1M-10M, 10M-100M, 100M+
    location = Column(String, nullable=True)  # Headquarters location
    is_hot = Column(Boolean, default=False)  # Hot/trending flag
    is_featured = Column(Boolean, default=False)  # Featured tool
    launch_date = Column(DateTime, nullable=True)  # When tool was launched
    
    # SEO fields
    meta_title = Column(String, nullable=True)
    meta_description = Column(String, nullable=True)
    slug = Column(String, unique=True, nullable=False)
    
    # AI-generated SEO content
    ai_meta_title = Column(String, nullable=True)
    ai_meta_description = Column(String, nullable=True)
    ai_content = Column(Text, nullable=True)
    
    # Tool assignment to admin
    assigned_admin_id = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    category = relationship("Category", back_populates="tools")
    subcategory = relationship("Subcategory", back_populates="tools")
    reviews = relationship("Review", back_populates="tool")
    compared_by_users = relationship("User", secondary=user_tool_comparison, back_populates="compared_tools")
    seo_optimizations = relationship("SEOOptimization", back_populates="tool")
    assigned_admin = relationship("User", foreign_keys=[assigned_admin_id], backref="assigned_tools")

class Blog(Base):
    __tablename__ = "blogs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(Text, nullable=True)
    status = Column(String, default="draft")  # draft, published, archived
    featured_image = Column(String, nullable=True)
    author_id = Column(String, ForeignKey("users.id"), nullable=False)
    category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    subcategory_id = Column(String, ForeignKey("subcategories.id"), nullable=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    reading_time = Column(Integer, default=0)  # in minutes
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # AI-generated content flag
    is_ai_generated = Column(Boolean, default=False)
    ai_prompt = Column(Text, nullable=True)  # Store the prompt used for AI generation
    
    # SEO fields
    meta_title = Column(String, nullable=True)
    meta_description = Column(String, nullable=True)
    slug = Column(String, unique=True, nullable=False)
    
    # Relationships
    author = relationship("User", back_populates="blogs")
    category = relationship("Category", back_populates="blogs")
    subcategory = relationship("Subcategory", back_populates="blogs")
    comments = relationship("Comment", back_populates="blog")
    reviews = relationship("BlogReview", back_populates="blog")
    liked_by_users = relationship("User", secondary=user_blog_likes, back_populates="liked_blogs")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    pros = Column(Text, nullable=True)
    cons = Column(Text, nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    tool_id = Column(String, ForeignKey("tools.id"), nullable=False)
    is_verified = Column(Boolean, default=False)
    helpful_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Ensure one review per user per tool
    __table_args__ = (UniqueConstraint('user_id', 'tool_id', name='unique_user_tool_review'),)
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    tool = relationship("Tool", back_populates="reviews")

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content = Column(Text, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    blog_id = Column(String, ForeignKey("blogs.id"), nullable=False)
    parent_id = Column(String, ForeignKey("comments.id"), nullable=True)  # for nested comments
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="comments")
    blog = relationship("Blog", back_populates="comments")
    parent = relationship("Comment", remote_side=[id])

class AIGeneratedContent(Base):
    __tablename__ = "ai_generated_content"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    content_type = Column(String, nullable=False)  # blog, tool_description, seo_content
    prompt = Column(Text, nullable=False)
    generated_content = Column(Text, nullable=False)
    provider = Column(String, nullable=False)  # groq, claude
    model = Column(String, nullable=True)  # Model used
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="ai_generated_content")

class SEOOptimization(Base):
    __tablename__ = "seo_optimizations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String, ForeignKey("tools.id"), nullable=False)
    target_keywords = Column(Text, nullable=True)  # JSON array of keywords
    meta_title = Column(String, nullable=True)
    meta_description = Column(String, nullable=True)
    content = Column(Text, nullable=True)
    search_engine = Column(String, nullable=False)  # google, bing
    optimization_score = Column(Float, default=0.0)
    generated_by = Column(String, nullable=False)  # groq, claude
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tool = relationship("Tool", back_populates="seo_optimizations")

class AdminSettings(Base):
    __tablename__ = "admin_settings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    setting_key = Column(String, unique=True, nullable=False)
    setting_value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class FreeTool(Base):
    __tablename__ = "free_tools"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    short_description = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    color = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    features = Column(Text, nullable=True)  # JSON string
    category = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    searches_count = Column(Integer, default=0)
    
    # SEO fields
    meta_title = Column(String, nullable=True)
    meta_description = Column(String, nullable=True)
    slug = Column(String, unique=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    search_history = relationship("SearchHistory", back_populates="tool")

class SearchHistory(Base):
    __tablename__ = "search_history"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String, ForeignKey("free_tools.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Optional for anonymous users
    search_engine = Column(String, nullable=False)  # google, bing
    query = Column(String, nullable=False)
    results_count = Column(Integer, default=0)
    results = Column(Text, nullable=True)  # JSON string
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tool = relationship("FreeTool", back_populates="search_history")
    user = relationship("User", backref="search_history")

class ToolComparison(Base):
    __tablename__ = "tool_comparison"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    tool_id = Column(String, ForeignKey("tools.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Ensure one comparison entry per user per tool
    __table_args__ = (UniqueConstraint('user_id', 'tool_id', name='unique_user_tool_comparison'),)
    
    # Relationships
    user = relationship("User", backref="tool_comparisons")
    tool = relationship("Tool", backref="comparisons")

class ToolAccessRequest(Base):
    __tablename__ = "tool_access_requests"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tool_id = Column(String, ForeignKey("tools.id"), nullable=False)
    admin_id = Column(String, ForeignKey("users.id"), nullable=False)  # Admin requesting access
    superadmin_id = Column(String, ForeignKey("users.id"), nullable=True)  # Superadmin who approved/denied
    status = Column(String, default="pending")  # pending, approved, denied
    request_message = Column(Text, nullable=True)  # Admin's reason for requesting
    response_message = Column(Text, nullable=True)  # Superadmin's response
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tool = relationship("Tool", backref="access_requests")
    admin = relationship("User", foreign_keys=[admin_id], backref="tool_access_requests")
    superadmin = relationship("User", foreign_keys=[superadmin_id], backref="processed_requests")