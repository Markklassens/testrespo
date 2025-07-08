from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, Float, Table
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    blogs = relationship("Blog", back_populates="author")
    reviews = relationship("Review", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    compared_tools = relationship("Tool", secondary=user_tool_comparison, back_populates="compared_by_users")

class Category(Base):
    __tablename__ = "categories"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)
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
    
    # SEO fields
    meta_title = Column(String, nullable=True)
    meta_description = Column(String, nullable=True)
    slug = Column(String, unique=True, nullable=False)
    
    # Relationships
    category = relationship("Category", back_populates="tools")
    subcategory = relationship("Subcategory", back_populates="tools")
    reviews = relationship("Review", back_populates="tool")
    compared_by_users = relationship("User", secondary=user_tool_comparison, back_populates="compared_tools")

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
    reading_time = Column(Integer, default=0)  # in minutes
    published_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # SEO fields
    meta_title = Column(String, nullable=True)
    meta_description = Column(String, nullable=True)
    slug = Column(String, unique=True, nullable=False)
    
    # Relationships
    author = relationship("User", back_populates="blogs")
    category = relationship("Category", back_populates="blogs")
    subcategory = relationship("Subcategory", back_populates="blogs")
    comments = relationship("Comment", back_populates="blog")

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