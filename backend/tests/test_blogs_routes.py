import pytest
from fastapi.testclient import TestClient
from models import Blog, Comment
import uuid

class TestBlogsRetrieval:
    """Test blog retrieval endpoints"""
    
    def test_get_blogs(self, client):
        """Test getting blogs"""
        response = client.get("/api/blogs")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_blogs_with_filters(self, client, test_category):
        """Test getting blogs with filters"""
        response = client.get(f"/api/blogs?category_id={test_category.id}&status=published")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_blogs_with_search(self, client):
        """Test getting blogs with search"""
        response = client.get("/api/blogs?search=test")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_blogs_with_sorting(self, client):
        """Test getting blogs with different sorting options"""
        sort_options = ["created_at", "views", "likes", "oldest"]
        
        for sort_by in sort_options:
            response = client.get(f"/api/blogs?sort_by={sort_by}")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data, list)
    
    def test_get_blogs_with_pagination(self, client):
        """Test getting blogs with pagination"""
        response = client.get("/api/blogs?skip=0&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_blog_by_id(self, client, test_blog):
        """Test getting blog by ID"""
        response = client.get(f"/api/blogs/{test_blog.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_blog.id
        assert data["title"] == test_blog.title
        assert data["content"] == test_blog.content
    
    def test_get_blog_by_id_not_found(self, client):
        """Test getting non-existent blog"""
        fake_blog_id = str(uuid.uuid4())
        response = client.get(f"/api/blogs/{fake_blog_id}")
        assert response.status_code == 404
        assert "Blog not found" in response.json()["detail"]
    
    def test_get_blog_by_slug(self, client, test_blog):
        """Test getting blog by slug"""
        response = client.get(f"/api/blogs/slug/{test_blog.slug}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_blog.id
        assert data["slug"] == test_blog.slug
    
    def test_get_blog_by_slug_not_found(self, client):
        """Test getting blog by non-existent slug"""
        response = client.get("/api/blogs/slug/non-existent-slug")
        assert response.status_code == 404
        assert "Blog not found" in response.json()["detail"]

class TestBlogsCreation:
    """Test blog creation endpoints"""
    
    def test_create_blog(self, client, test_user, test_category, auth_headers):
        """Test creating a new blog"""
        blog_data = {
            "title": "New Blog Post",
            "content": "This is the content of the new blog post. It has multiple sentences to test reading time calculation.",
            "excerpt": "This is a short excerpt",
            "status": "published",
            "category_id": test_category.id,
            "slug": "new-blog-post"
        }
        
        response = client.post("/api/blogs", json=blog_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == blog_data["title"]
        assert data["content"] == blog_data["content"]
        assert data["excerpt"] == blog_data["excerpt"]
        assert data["status"] == blog_data["status"]
        assert data["category_id"] == blog_data["category_id"]
        assert data["slug"] == blog_data["slug"]
        assert data["author_id"] == test_user.id
        assert data["reading_time"] > 0
    
    def test_create_blog_unauthorized(self, client, test_category):
        """Test creating blog without authentication"""
        blog_data = {
            "title": "New Blog Post",
            "content": "This is the content of the new blog post.",
            "category_id": test_category.id,
            "slug": "new-blog-post"
        }
        
        response = client.post("/api/blogs", json=blog_data)
        assert response.status_code == 401
    
    def test_create_blog_duplicate_slug(self, client, test_blog, test_category, auth_headers):
        """Test creating blog with duplicate slug"""
        blog_data = {
            "title": "Another Blog Post",
            "content": "This is different content.",
            "category_id": test_category.id,
            "slug": test_blog.slug
        }
        
        response = client.post("/api/blogs", json=blog_data, headers=auth_headers)
        assert response.status_code == 400
        assert "Slug already exists" in response.json()["detail"]
    
    def test_create_blog_draft(self, client, test_user, test_category, auth_headers):
        """Test creating a draft blog"""
        blog_data = {
            "title": "Draft Blog Post",
            "content": "This is a draft blog post.",
            "status": "draft",
            "category_id": test_category.id,
            "slug": "draft-blog-post"
        }
        
        response = client.post("/api/blogs", json=blog_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "draft"
        assert data["published_at"] is None

class TestBlogsUpdate:
    """Test blog update endpoints"""
    
    def test_update_blog(self, client, test_blog, test_user, auth_headers):
        """Test updating a blog"""
        update_data = {
            "title": "Updated Blog Title",
            "content": "This is the updated content of the blog post.",
            "excerpt": "Updated excerpt"
        }
        
        response = client.put(f"/api/blogs/{test_blog.id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["content"] == update_data["content"]
        assert data["excerpt"] == update_data["excerpt"]
    
    def test_update_blog_not_found(self, client, auth_headers):
        """Test updating non-existent blog"""
        fake_blog_id = str(uuid.uuid4())
        update_data = {
            "title": "Updated Title"
        }
        
        response = client.put(f"/api/blogs/{fake_blog_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 404
        assert "Blog not found" in response.json()["detail"]
    
    def test_update_blog_unauthorized(self, client, test_blog):
        """Test updating blog without authentication"""
        update_data = {
            "title": "Updated Title"
        }
        
        response = client.put(f"/api/blogs/{test_blog.id}", json=update_data)
        assert response.status_code == 401
    
    def test_update_blog_forbidden(self, client, test_blog, test_user, auth_headers, db):
        """Test updating blog by different user"""
        # Create another user
        from auth import get_password_hash
        from models import User
        another_user = User(
            id=str(uuid.uuid4()),
            email="another@example.com",
            username="anotheruser",
            full_name="Another User",
            hashed_password=get_password_hash("password123"),
            user_type="user",
            is_active=True,
            is_verified=True
        )
        db.add(another_user)
        db.commit()
        
        # Login as another user
        login_response = client.post("/api/auth/login", json={
            "email": another_user.email,
            "password": "password123"
        })
        another_token = login_response.json()["access_token"]
        another_headers = {"Authorization": f"Bearer {another_token}"}
        
        update_data = {
            "title": "Updated Title"
        }
        
        response = client.put(f"/api/blogs/{test_blog.id}", json=update_data, headers=another_headers)
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    def test_update_blog_status_to_published(self, client, test_user, test_category, auth_headers):
        """Test updating blog status to published"""
        # Create a draft blog
        blog_data = {
            "title": "Draft Blog",
            "content": "Draft content",
            "status": "draft",
            "category_id": test_category.id,
            "slug": "draft-blog"
        }
        
        create_response = client.post("/api/blogs", json=blog_data, headers=auth_headers)
        blog_id = create_response.json()["id"]
        
        # Update status to published
        update_data = {
            "status": "published"
        }
        
        response = client.put(f"/api/blogs/{blog_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "published"
        assert data["published_at"] is not None

class TestBlogsDeletion:
    """Test blog deletion endpoints"""
    
    def test_delete_blog(self, client, test_blog, auth_headers):
        """Test deleting a blog"""
        response = client.delete(f"/api/blogs/{test_blog.id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Blog deleted successfully"
    
    def test_delete_blog_not_found(self, client, auth_headers):
        """Test deleting non-existent blog"""
        fake_blog_id = str(uuid.uuid4())
        response = client.delete(f"/api/blogs/{fake_blog_id}", headers=auth_headers)
        assert response.status_code == 404
        assert "Blog not found" in response.json()["detail"]
    
    def test_delete_blog_unauthorized(self, client, test_blog):
        """Test deleting blog without authentication"""
        response = client.delete(f"/api/blogs/{test_blog.id}")
        assert response.status_code == 401

class TestBlogsInteractions:
    """Test blog interaction endpoints"""
    
    def test_like_blog(self, client, test_blog, auth_headers):
        """Test liking a blog"""
        response = client.post(f"/api/blogs/{test_blog.id}/like", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "likes" in data
        assert data["likes"] == test_blog.likes + 1
    
    def test_like_blog_not_found(self, client, auth_headers):
        """Test liking non-existent blog"""
        fake_blog_id = str(uuid.uuid4())
        response = client.post(f"/api/blogs/{fake_blog_id}/like", headers=auth_headers)
        assert response.status_code == 404
        assert "Blog not found" in response.json()["detail"]
    
    def test_like_blog_unauthorized(self, client, test_blog):
        """Test liking blog without authentication"""
        response = client.post(f"/api/blogs/{test_blog.id}/like")
        assert response.status_code == 401

class TestBlogsComments:
    """Test blog comments endpoints"""
    
    def test_create_comment(self, client, test_blog, test_user, auth_headers):
        """Test creating a comment on a blog"""
        comment_data = {
            "content": "This is a great blog post!",
            "blog_id": test_blog.id
        }
        
        response = client.post(f"/api/blogs/{test_blog.id}/comments", json=comment_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["content"] == comment_data["content"]
        assert data["blog_id"] == test_blog.id
        assert data["user_id"] == test_user.id
    
    def test_create_comment_blog_not_found(self, client, auth_headers):
        """Test creating comment on non-existent blog"""
        fake_blog_id = str(uuid.uuid4())
        comment_data = {
            "content": "This is a comment",
            "blog_id": fake_blog_id
        }
        
        response = client.post(f"/api/blogs/{fake_blog_id}/comments", json=comment_data, headers=auth_headers)
        assert response.status_code == 404
        assert "Blog not found" in response.json()["detail"]
    
    def test_create_comment_unauthorized(self, client, test_blog):
        """Test creating comment without authentication"""
        comment_data = {
            "content": "This is a comment",
            "blog_id": test_blog.id
        }
        
        response = client.post(f"/api/blogs/{test_blog.id}/comments", json=comment_data)
        assert response.status_code == 401
    
    def test_get_blog_comments(self, client, test_blog):
        """Test getting comments for a blog"""
        response = client.get(f"/api/blogs/{test_blog.id}/comments")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_blog_comments_with_pagination(self, client, test_blog):
        """Test getting comments with pagination"""
        response = client.get(f"/api/blogs/{test_blog.id}/comments?skip=0&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_comment_not_found(self, client, auth_headers):
        """Test updating non-existent comment"""
        fake_comment_id = str(uuid.uuid4())
        update_data = {
            "content": "Updated comment content",
            "blog_id": str(uuid.uuid4())
        }
        
        response = client.put(f"/api/blogs/comments/{fake_comment_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 404
        assert "Comment not found" in response.json()["detail"]
    
    def test_delete_comment_not_found(self, client, auth_headers):
        """Test deleting non-existent comment"""
        fake_comment_id = str(uuid.uuid4())
        response = client.delete(f"/api/blogs/comments/{fake_comment_id}", headers=auth_headers)
        assert response.status_code == 404
        assert "Comment not found" in response.json()["detail"]

class TestBlogsAnalytics:
    """Test blog analytics endpoints"""
    
    def test_get_blog_analytics_stats(self, client, auth_headers):
        """Test getting blog analytics statistics"""
        response = client.get("/api/blogs/analytics/stats", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_stats" in data
        assert "user_stats" in data
        assert "popular_content" in data
        
        # Check total stats structure
        total_stats = data["total_stats"]
        assert "total_blogs" in total_stats
        assert "published_blogs" in total_stats
        assert "draft_blogs" in total_stats
        
        # Check user stats structure
        user_stats = data["user_stats"]
        assert "user_blogs" in user_stats
        assert "user_published" in user_stats
        assert "user_drafts" in user_stats
        
        # Check popular content structure
        popular_content = data["popular_content"]
        assert "most_viewed" in popular_content
        assert "most_liked" in popular_content
        assert "recent_blogs" in popular_content
    
    def test_get_blog_analytics_unauthorized(self, client):
        """Test getting blog analytics without authentication"""
        response = client.get("/api/blogs/analytics/stats")
        assert response.status_code == 401
    
    def test_get_blog_category_stats(self, client):
        """Test getting blog category statistics"""
        response = client.get("/api/blogs/categories/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_author_stats(self, client, auth_headers):
        """Test getting author statistics"""
        response = client.get("/api/blogs/authors/stats", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "user_stats" in data
        
        user_stats = data["user_stats"]
        assert "author_id" in user_stats
        assert "author_name" in user_stats
        assert "blog_count" in user_stats
        assert "total_views" in user_stats
        assert "total_likes" in user_stats
    
    def test_get_trending_blogs(self, client):
        """Test getting trending blogs"""
        response = client.get("/api/blogs/trending")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_trending_blogs_with_limit(self, client):
        """Test getting trending blogs with limit"""
        response = client.get("/api/blogs/trending?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)