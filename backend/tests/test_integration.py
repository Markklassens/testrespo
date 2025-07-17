import pytest
from fastapi.testclient import TestClient
from models import User, Tool, Blog, Category, FreeTool
import uuid

class TestIntegration:
    """Integration tests for the complete API"""
    
    def test_complete_user_workflow(self, client, test_category, db):
        """Test complete user registration and usage workflow"""
        # 1. Register a new user
        user_data = {
            "email": "integration@example.com",
            "username": "integrationuser",
            "full_name": "Integration User",
            "password": "integrationpass123",
            "user_type": "user"
        }
        
        register_response = client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # 2. Login with the new user
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        login_response = client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Get user profile
        profile_response = client.get("/api/auth/me", headers=headers)
        assert profile_response.status_code == 200
        
        # 4. Update user profile
        update_data = {
            "full_name": "Updated Integration User"
        }
        
        update_response = client.put("/api/user/profile", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        # 5. Get dashboard stats
        stats_response = client.get("/api/user/dashboard-stats", headers=headers)
        assert stats_response.status_code == 200
        
        # 6. Create a blog post
        blog_data = {
            "title": "Integration Test Blog",
            "content": "This is a test blog post for integration testing.",
            "status": "published",
            "category_id": test_category.id,
            "slug": "integration-test-blog"
        }
        
        blog_response = client.post("/api/blogs", json=blog_data, headers=headers)
        assert blog_response.status_code == 200
        blog_id = blog_response.json()["id"]
        
        # 7. Like the blog post
        like_response = client.post(f"/api/blogs/{blog_id}/like", headers=headers)
        assert like_response.status_code == 200
        
        # 8. Comment on the blog post
        comment_data = {
            "content": "This is a test comment",
            "blog_id": blog_id
        }
        
        comment_response = client.post(f"/api/blogs/{blog_id}/comments", json=comment_data, headers=headers)
        assert comment_response.status_code == 200
    
    def test_complete_admin_workflow(self, client, test_category, db):
        """Test complete admin workflow"""
        # 1. Create admin user
        admin_data = {
            "email": "integrationadmin@example.com",
            "username": "integrationadmin",
            "full_name": "Integration Admin",
            "password": "adminpass123",
            "user_type": "admin"
        }
        
        register_response = client.post("/api/auth/register", json=admin_data)
        assert register_response.status_code == 200
        
        # 2. Login as admin
        login_data = {
            "email": admin_data["email"],
            "password": admin_data["password"]
        }
        
        login_response = client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create a free tool
        tool_data = {
            "name": "Integration Test Tool",
            "description": "Test tool for integration testing",
            "slug": "integration-test-tool",
            "is_active": True
        }
        
        tool_response = client.post("/api/admin/free-tools", json=tool_data, headers=headers)
        assert tool_response.status_code == 200
        tool_id = tool_response.json()["id"]
        
        # 4. Update the tool
        update_data = {
            "name": "Updated Integration Test Tool"
        }
        
        update_response = client.put(f"/api/admin/free-tools/{tool_id}", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        # 5. Get admin analytics
        analytics_response = client.get("/api/admin/free-tools/analytics", headers=headers)
        assert analytics_response.status_code == 200
        
        # 6. Get all reviews
        reviews_response = client.get("/api/admin/reviews", headers=headers)
        assert reviews_response.status_code == 200
        
        # 7. Get SEO tools
        seo_response = client.get("/api/admin/seo/tools", headers=headers)
        assert seo_response.status_code == 200
    
    def test_complete_superadmin_workflow(self, client, test_category, db):
        """Test complete superadmin workflow"""
        # 1. Create superadmin user
        superadmin_data = {
            "email": "integrationsuperadmin@example.com",
            "username": "integrationsuperadmin",
            "full_name": "Integration Superadmin",
            "password": "superadminpass123",
            "user_type": "superadmin"
        }
        
        register_response = client.post("/api/auth/register", json=superadmin_data)
        assert register_response.status_code == 200
        
        # 2. Login as superadmin
        login_data = {
            "email": superadmin_data["email"],
            "password": superadmin_data["password"]
        }
        
        login_response = client.post("/api/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create a regular user
        user_data = {
            "email": "createduser@example.com",
            "username": "createduser",
            "full_name": "Created User",
            "password": "createdpass123",
            "user_type": "user"
        }
        
        user_response = client.post("/api/superadmin/users", json=user_data, headers=headers)
        assert user_response.status_code == 200
        user_id = user_response.json()["id"]
        
        # 4. Promote user to admin
        promote_response = client.post(f"/api/superadmin/users/{user_id}/promote", headers=headers)
        assert promote_response.status_code == 200
        
        # 5. Get all users
        users_response = client.get("/api/superadmin/users", headers=headers)
        assert users_response.status_code == 200
        
        # 6. Get advanced analytics
        analytics_response = client.get("/api/superadmin/analytics/advanced", headers=headers)
        assert analytics_response.status_code == 200
        
        # 7. Create a category
        category_data = {
            "name": "Integration Category",
            "description": "Category for integration testing",
            "icon": "test-icon",
            "color": "#FF0000"
        }
        
        category_response = client.post("/api/superadmin/categories", json=category_data, headers=headers)
        assert category_response.status_code == 200
        category_id = category_response.json()["id"]
        
        # 8. Update the category
        update_data = {
            "name": "Updated Integration Category"
        }
        
        update_response = client.put(f"/api/superadmin/categories/{category_id}", json=update_data, headers=headers)
        assert update_response.status_code == 200
        
        # 9. Get trending stats
        trending_response = client.get("/api/superadmin/tools/trending-stats", headers=headers)
        assert trending_response.status_code == 200
        
        # 10. Get tool access requests
        requests_response = client.get("/api/superadmin/tools/access-requests", headers=headers)
        assert requests_response.status_code == 200
    
    def test_public_endpoints_accessibility(self, client):
        """Test that public endpoints are accessible without authentication"""
        public_endpoints = [
            "/api/health",
            "/api/tools/analytics",
            "/api/tools/search",
            "/api/tools/categories",
            "/api/tools/categories/analytics",
            "/api/free-tools",
            "/api/blogs",
            "/api/blogs/trending",
            "/api/blogs/categories/stats"
        ]
        
        for endpoint in public_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Public endpoint {endpoint} should be accessible"
    
    def test_authentication_required_endpoints(self, client):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            "/api/auth/me",
            "/api/user/profile",
            "/api/user/dashboard-stats",
            "/api/admin/reviews",
            "/api/admin/seo/tools",
            "/api/superadmin/users",
            "/api/superadmin/analytics/advanced"
        ]
        
        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Protected endpoint {endpoint} should require authentication"
    
    def test_role_based_access_control(self, client, test_user, test_admin, test_superadmin):
        """Test role-based access control across different endpoints"""
        # Get tokens for different user types
        user_response = client.post("/api/auth/login", json={
            "email": test_user.email,
            "password": "testpass123"
        })
        user_token = user_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        admin_response = client.post("/api/auth/login", json={
            "email": test_admin.email,
            "password": "adminpass123"
        })
        admin_token = admin_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        superadmin_response = client.post("/api/auth/login", json={
            "email": test_superadmin.email,
            "password": "superadminpass123"
        })
        superadmin_token = superadmin_response.json()["access_token"]
        superadmin_headers = {"Authorization": f"Bearer {superadmin_token}"}
        
        # Test user access
        user_accessible = [
            "/api/auth/me",
            "/api/user/profile",
            "/api/user/dashboard-stats"
        ]
        
        for endpoint in user_accessible:
            response = client.get(endpoint, headers=user_headers)
            assert response.status_code == 200, f"User should access {endpoint}"
        
        # Test admin access
        admin_accessible = [
            "/api/admin/reviews",
            "/api/admin/seo/tools",
            "/api/admin/free-tools/analytics"
        ]
        
        for endpoint in admin_accessible:
            response = client.get(endpoint, headers=admin_headers)
            assert response.status_code == 200, f"Admin should access {endpoint}"
        
        # Test superadmin access
        superadmin_accessible = [
            "/api/superadmin/users",
            "/api/superadmin/analytics/advanced",
            "/api/superadmin/tools/trending-stats"
        ]
        
        for endpoint in superadmin_accessible:
            response = client.get(endpoint, headers=superadmin_headers)
            assert response.status_code == 200, f"Superadmin should access {endpoint}"
        
        # Test access restrictions
        # User should not access admin endpoints
        for endpoint in admin_accessible:
            response = client.get(endpoint, headers=user_headers)
            assert response.status_code == 403, f"User should not access {endpoint}"
        
        # Admin should not access superadmin endpoints
        for endpoint in superadmin_accessible:
            response = client.get(endpoint, headers=admin_headers)
            assert response.status_code == 403, f"Admin should not access {endpoint}"