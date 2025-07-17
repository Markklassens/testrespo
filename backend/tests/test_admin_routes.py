import pytest
from fastapi.testclient import TestClient
from models import Tool, Review, FreeTool, ToolAccessRequest
import uuid

class TestAdminToolManagement:
    """Test admin tool management endpoints"""
    
    def test_update_tool_content_unauthorized(self, client, test_tool):
        """Test updating tool content without authentication"""
        update_data = {
            "description": "Updated description"
        }
        
        response = client.put(f"/api/admin/tools/{test_tool.id}/content", json=update_data)
        assert response.status_code == 401
    
    def test_update_tool_content_no_access(self, client, test_tool, auth_headers):
        """Test updating tool content without access"""
        update_data = {
            "description": "Updated description"
        }
        
        response = client.put(f"/api/admin/tools/{test_tool.id}/content", json=update_data, headers=auth_headers)
        assert response.status_code == 403
        assert "You don't have access to this tool" in response.json()["detail"]
    
    def test_request_tool_access(self, client, test_tool, test_admin, admin_headers):
        """Test requesting access to a tool"""
        request_data = {
            "tool_id": test_tool.id,
            "request_message": "I need access to this tool for content management"
        }
        
        response = client.post(f"/api/admin/tools/{test_tool.id}/request-access", json=request_data, headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["tool_id"] == test_tool.id
        assert data["admin_id"] == test_admin.id
        assert data["status"] == "pending"
    
    def test_request_tool_access_duplicate(self, client, test_tool, test_admin, admin_headers, db):
        """Test requesting access to a tool that already has pending request"""
        # Create existing request
        existing_request = ToolAccessRequest(
            id=str(uuid.uuid4()),
            tool_id=test_tool.id,
            admin_id=test_admin.id,
            status="pending"
        )
        db.add(existing_request)
        db.commit()
        
        request_data = {
            "tool_id": test_tool.id,
            "request_message": "I need access to this tool"
        }
        
        response = client.post(f"/api/admin/tools/{test_tool.id}/request-access", json=request_data, headers=admin_headers)
        assert response.status_code == 400
        assert "already have a pending request" in response.json()["detail"]
    
    def test_get_my_tool_requests(self, client, test_admin, admin_headers):
        """Test getting admin's tool access requests"""
        response = client.get("/api/admin/tools/my-requests", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

class TestAdminReviewManagement:
    """Test admin review management endpoints"""
    
    def test_get_all_reviews(self, client, admin_headers):
        """Test getting all reviews"""
        response = client.get("/api/admin/reviews", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_reviews_with_filters(self, client, test_tool, admin_headers):
        """Test getting reviews with filters"""
        response = client.get(f"/api/admin/reviews?tool_id={test_tool.id}&is_verified=true", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_verify_review_not_found(self, client, admin_headers):
        """Test verifying non-existent review"""
        fake_review_id = str(uuid.uuid4())
        response = client.put(f"/api/admin/reviews/{fake_review_id}/verify", headers=admin_headers)
        assert response.status_code == 404
        assert "Review not found" in response.json()["detail"]
    
    def test_delete_review_not_found(self, client, admin_headers):
        """Test deleting non-existent review"""
        fake_review_id = str(uuid.uuid4())
        response = client.delete(f"/api/admin/reviews/{fake_review_id}", headers=admin_headers)
        assert response.status_code == 404
        assert "Review not found" in response.json()["detail"]

class TestAdminSEOManagement:
    """Test admin SEO management endpoints"""
    
    def test_get_seo_optimizations(self, client, admin_headers):
        """Test getting SEO optimizations"""
        response = client.get("/api/admin/seo/optimizations", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_seo_tools(self, client, admin_headers):
        """Test getting SEO tools status"""
        response = client.get("/api/admin/seo/tools", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_optimize_tool_seo_no_access(self, client, test_tool, admin_headers):
        """Test SEO optimization without tool access"""
        seo_request = {
            "tool_id": test_tool.id,
            "target_keywords": ["test", "tool"],
            "search_engine": "google"
        }
        
        response = client.post("/api/admin/seo/optimize", json=seo_request, headers=admin_headers)
        assert response.status_code == 403
        assert "You don't have access to this tool" in response.json()["detail"]

class TestAdminFreeToolsManagement:
    """Test admin free tools management endpoints"""
    
    def test_create_free_tool(self, client, admin_headers):
        """Test creating a free tool"""
        tool_data = {
            "name": "New Free Tool",
            "description": "Description for new free tool",
            "slug": "new-free-tool",
            "is_active": True
        }
        
        response = client.post("/api/admin/free-tools", json=tool_data, headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == tool_data["name"]
        assert data["slug"] == tool_data["slug"]
        assert data["is_active"] == tool_data["is_active"]
    
    def test_create_free_tool_duplicate_slug(self, client, test_free_tool, admin_headers):
        """Test creating free tool with duplicate slug"""
        tool_data = {
            "name": "Another Tool",
            "description": "Another description",
            "slug": test_free_tool.slug,
            "is_active": True
        }
        
        response = client.post("/api/admin/free-tools", json=tool_data, headers=admin_headers)
        assert response.status_code == 400
        assert "Slug already exists" in response.json()["detail"]
    
    def test_update_free_tool(self, client, test_free_tool, admin_headers):
        """Test updating a free tool"""
        update_data = {
            "name": "Updated Free Tool Name",
            "description": "Updated description"
        }
        
        response = client.put(f"/api/admin/free-tools/{test_free_tool.id}", json=update_data, headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
    
    def test_update_free_tool_not_found(self, client, admin_headers):
        """Test updating non-existent free tool"""
        fake_tool_id = str(uuid.uuid4())
        update_data = {
            "name": "Updated Name"
        }
        
        response = client.put(f"/api/admin/free-tools/{fake_tool_id}", json=update_data, headers=admin_headers)
        assert response.status_code == 404
        assert "Free tool not found" in response.json()["detail"]
    
    def test_delete_free_tool(self, client, test_free_tool, admin_headers):
        """Test deleting a free tool"""
        response = client.delete(f"/api/admin/free-tools/{test_free_tool.id}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Free tool deleted successfully"
    
    def test_delete_free_tool_not_found(self, client, admin_headers):
        """Test deleting non-existent free tool"""
        fake_tool_id = str(uuid.uuid4())
        response = client.delete(f"/api/admin/free-tools/{fake_tool_id}", headers=admin_headers)
        assert response.status_code == 404
        assert "Free tool not found" in response.json()["detail"]
    
    def test_get_all_free_tools_admin(self, client, admin_headers):
        """Test getting all free tools as admin"""
        response = client.get("/api/admin/free-tools", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_free_tools_analytics(self, client, admin_headers):
        """Test getting free tools analytics"""
        response = client.get("/api/admin/free-tools/analytics", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_tools" in data
        assert "active_tools" in data
        assert "total_searches" in data
        assert "total_views" in data
        assert "popular_tools" in data
        assert "recent_searches" in data
    
    def test_get_tool_search_history(self, client, test_free_tool, admin_headers):
        """Test getting search history for a tool"""
        response = client.get(f"/api/admin/free-tools/{test_free_tool.id}/search-history", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

class TestAdminAuth:
    """Test admin authentication requirements"""
    
    def test_admin_required_endpoints(self, client, auth_headers):
        """Test that admin endpoints require admin role"""
        endpoints = [
            "/api/admin/reviews",
            "/api/admin/seo/tools",
            "/api/admin/free-tools",
            "/api/admin/free-tools/analytics"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 403
            assert "Not enough permissions" in response.json()["detail"]