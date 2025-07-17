import pytest
from fastapi.testclient import TestClient
from models import Tool, Review, FreeTool, SearchHistory
import uuid

class TestToolsAnalytics:
    """Test tools analytics endpoints"""
    
    def test_get_tools_analytics(self, client):
        """Test getting tools analytics"""
        response = client.get("/api/tools/analytics")
        assert response.status_code == 200
        
        data = response.json()
        assert "trending_tools" in data
        assert "top_rated_tools" in data
        assert "most_viewed_tools" in data
        assert "newest_tools" in data
        assert "featured_tools" in data
        assert "hot_tools" in data
        
        # Check that each field is a list
        for field in data:
            assert isinstance(data[field], list)
    
    def test_get_tools_analytics_with_recalculation(self, client):
        """Test getting tools analytics with recalculation"""
        response = client.get("/api/tools/analytics?recalculate=true")
        assert response.status_code == 200
        
        data = response.json()
        assert "trending_tools" in data

class TestToolsSearch:
    """Test tools search endpoints"""
    
    def test_advanced_search_basic(self, client):
        """Test basic advanced search"""
        response = client.get("/api/tools/search")
        assert response.status_code == 200
        
        data = response.json()
        assert "tools" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data
        assert "has_next" in data
        assert "has_prev" in data
        assert isinstance(data["tools"], list)
    
    def test_advanced_search_with_query(self, client):
        """Test advanced search with query"""
        response = client.get("/api/tools/search?q=test")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["tools"], list)
    
    def test_advanced_search_with_filters(self, client, test_category):
        """Test advanced search with filters"""
        response = client.get(f"/api/tools/search?category_id={test_category.id}&pricing_model=Freemium")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["tools"], list)
    
    def test_advanced_search_with_sorting(self, client):
        """Test advanced search with sorting"""
        sort_options = ["rating", "trending", "views", "newest", "oldest", "name"]
        
        for sort_by in sort_options:
            response = client.get(f"/api/tools/search?sort_by={sort_by}")
            assert response.status_code == 200
            
            data = response.json()
            assert isinstance(data["tools"], list)
    
    def test_advanced_search_with_pagination(self, client):
        """Test advanced search with pagination"""
        response = client.get("/api/tools/search?page=1&per_page=10")
        assert response.status_code == 200
        
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10
        assert isinstance(data["tools"], list)
    
    def test_advanced_search_with_rating_filter(self, client):
        """Test advanced search with rating filter"""
        response = client.get("/api/tools/search?min_rating=3.0")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["tools"], list)
    
    def test_advanced_search_with_boolean_filters(self, client):
        """Test advanced search with boolean filters"""
        response = client.get("/api/tools/search?is_hot=true&is_featured=false")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["tools"], list)

class TestToolsRetrieval:
    """Test individual tool retrieval endpoints"""
    
    def test_get_tool_by_id(self, client, test_tool):
        """Test getting tool by ID"""
        response = client.get(f"/api/tools/{test_tool.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_tool.id
        assert data["name"] == test_tool.name
        assert data["description"] == test_tool.description
    
    def test_get_tool_by_id_not_found(self, client):
        """Test getting non-existent tool"""
        fake_tool_id = str(uuid.uuid4())
        response = client.get(f"/api/tools/{fake_tool_id}")
        assert response.status_code == 404
        assert "Tool not found" in response.json()["detail"]
    
    def test_get_tool_by_slug(self, client, test_tool):
        """Test getting tool by slug"""
        response = client.get(f"/api/tools/slug/{test_tool.slug}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_tool.id
        assert data["slug"] == test_tool.slug
    
    def test_get_tool_by_slug_not_found(self, client):
        """Test getting tool by non-existent slug"""
        response = client.get("/api/tools/slug/non-existent-slug")
        assert response.status_code == 404
        assert "Tool not found" in response.json()["detail"]

class TestToolsReviews:
    """Test tool review endpoints"""
    
    def test_create_review(self, client, test_tool, test_user, auth_headers):
        """Test creating a review for a tool"""
        review_data = {
            "rating": 5,
            "title": "Great tool!",
            "content": "This tool is amazing and very useful.",
            "pros": "Easy to use, great features",
            "cons": "Could be faster",
            "tool_id": test_tool.id
        }
        
        response = client.post(f"/api/tools/{test_tool.id}/reviews", json=review_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["rating"] == review_data["rating"]
        assert data["title"] == review_data["title"]
        assert data["content"] == review_data["content"]
        assert data["user_id"] == test_user.id
        assert data["tool_id"] == test_tool.id
    
    def test_create_review_tool_not_found(self, client, auth_headers):
        """Test creating review for non-existent tool"""
        fake_tool_id = str(uuid.uuid4())
        review_data = {
            "rating": 5,
            "title": "Great tool!",
            "content": "This tool is amazing.",
            "tool_id": fake_tool_id
        }
        
        response = client.post(f"/api/tools/{fake_tool_id}/reviews", json=review_data, headers=auth_headers)
        assert response.status_code == 404
        assert "Tool not found" in response.json()["detail"]
    
    def test_create_review_unauthorized(self, client, test_tool):
        """Test creating review without authentication"""
        review_data = {
            "rating": 5,
            "title": "Great tool!",
            "content": "This tool is amazing.",
            "tool_id": test_tool.id
        }
        
        response = client.post(f"/api/tools/{test_tool.id}/reviews", json=review_data)
        assert response.status_code == 401
    
    def test_create_duplicate_review(self, client, test_tool, test_user, auth_headers, db):
        """Test creating duplicate review for same tool"""
        # Create first review
        review_data = {
            "rating": 5,
            "title": "Great tool!",
            "content": "This tool is amazing.",
            "tool_id": test_tool.id
        }
        
        response = client.post(f"/api/tools/{test_tool.id}/reviews", json=review_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Try to create second review
        response = client.post(f"/api/tools/{test_tool.id}/reviews", json=review_data, headers=auth_headers)
        assert response.status_code == 400
        assert "You have already reviewed this tool" in response.json()["detail"]
    
    def test_get_tool_reviews(self, client, test_tool):
        """Test getting reviews for a tool"""
        response = client.get(f"/api/tools/{test_tool.id}/reviews")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_tool_reviews_with_pagination(self, client, test_tool):
        """Test getting reviews with pagination"""
        response = client.get(f"/api/tools/{test_tool.id}/reviews?skip=0&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_review_not_found(self, client, auth_headers):
        """Test updating non-existent review"""
        fake_review_id = str(uuid.uuid4())
        update_data = {
            "rating": 4,
            "title": "Updated title",
            "content": "Updated content",
            "tool_id": str(uuid.uuid4())
        }
        
        response = client.put(f"/api/tools/reviews/{fake_review_id}", json=update_data, headers=auth_headers)
        assert response.status_code == 404
        assert "Review not found" in response.json()["detail"]
    
    def test_delete_review_not_found(self, client, auth_headers):
        """Test deleting non-existent review"""
        fake_review_id = str(uuid.uuid4())
        response = client.delete(f"/api/tools/reviews/{fake_review_id}", headers=auth_headers)
        assert response.status_code == 404
        assert "Review not found" in response.json()["detail"]

class TestToolsCategories:
    """Test tool categories endpoints"""
    
    def test_get_categories(self, client):
        """Test getting all categories"""
        response = client.get("/api/tools/categories")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_category_analytics(self, client):
        """Test getting category analytics"""
        response = client.get("/api/tools/categories/analytics")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # Check structure of analytics if data exists
        if data:
            analytics = data[0]
            assert "category_id" in analytics
            assert "category_name" in analytics
            assert "tool_count" in analytics
            assert "avg_rating" in analytics
            assert "total_views" in analytics
            assert "recommended_tools" in analytics

class TestFreeTools:
    """Test free tools endpoints"""
    
    def test_get_free_tools(self, client):
        """Test getting free tools"""
        response = client.get("/api/free-tools")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_free_tools_with_filters(self, client):
        """Test getting free tools with filters"""
        response = client.get("/api/free-tools?category=search&search=test")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_free_tools_with_pagination(self, client):
        """Test getting free tools with pagination"""
        response = client.get("/api/free-tools?skip=0&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_free_tools_inactive(self, client):
        """Test getting inactive free tools"""
        response = client.get("/api/free-tools?is_active=false")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_free_tool_by_id(self, client, test_free_tool):
        """Test getting free tool by ID"""
        response = client.get(f"/api/free-tools/{test_free_tool.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_free_tool.id
        assert data["name"] == test_free_tool.name
    
    def test_get_free_tool_by_id_not_found(self, client):
        """Test getting non-existent free tool"""
        fake_tool_id = str(uuid.uuid4())
        response = client.get(f"/api/free-tools/{fake_tool_id}")
        assert response.status_code == 404
        assert "Free tool not found" in response.json()["detail"]
    
    def test_get_free_tool_by_slug(self, client, test_free_tool):
        """Test getting free tool by slug"""
        response = client.get(f"/api/free-tools/slug/{test_free_tool.slug}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_free_tool.id
        assert data["slug"] == test_free_tool.slug
    
    def test_get_free_tool_by_slug_not_found(self, client):
        """Test getting free tool by non-existent slug"""
        response = client.get("/api/free-tools/slug/non-existent-slug")
        assert response.status_code == 404
        assert "Free tool not found" in response.json()["detail"]

class TestFreeToolsSearch:
    """Test free tools search functionality"""
    
    def test_search_with_tool_invalid_engine(self, client, test_free_tool):
        """Test search with invalid engine"""
        search_data = {
            "query": "test query",
            "engine": "invalid_engine",
            "num_results": 10
        }
        
        response = client.post(f"/api/free-tools/{test_free_tool.id}/search", json=search_data)
        assert response.status_code == 400
        assert "Invalid search engine" in response.json()["detail"]
    
    def test_search_with_tool_not_found(self, client):
        """Test search with non-existent tool"""
        fake_tool_id = str(uuid.uuid4())
        search_data = {
            "query": "test query",
            "engine": "google",
            "num_results": 10
        }
        
        response = client.post(f"/api/free-tools/{fake_tool_id}/search", json=search_data)
        assert response.status_code == 404
        assert "Free tool not found" in response.json()["detail"]
    
    def test_combined_search_with_tool_not_found(self, client):
        """Test combined search with non-existent tool"""
        fake_tool_id = str(uuid.uuid4())
        search_data = {
            "query": "test query",
            "num_results": 10
        }
        
        response = client.post(f"/api/free-tools/{fake_tool_id}/search/combined", json=search_data)
        assert response.status_code == 404
        assert "Free tool not found" in response.json()["detail"]

class TestToolsPublicAccess:
    """Test public access to tools endpoints"""
    
    def test_public_endpoints_no_auth_required(self, client):
        """Test that public endpoints don't require authentication"""
        public_endpoints = [
            "/api/tools/analytics",
            "/api/tools/search",
            "/api/tools/categories",
            "/api/tools/categories/analytics",
            "/api/free-tools"
        ]
        
        for endpoint in public_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200