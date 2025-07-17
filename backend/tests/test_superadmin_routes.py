import pytest
from fastapi.testclient import TestClient
from models import User, Category, ToolAccessRequest
import uuid

class TestSuperAdminUserManagement:
    """Test super admin user management endpoints"""
    
    def test_get_all_users(self, client, superadmin_headers):
        """Test getting all users"""
        response = client.get("/api/superadmin/users", headers=superadmin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_users_with_filters(self, client, superadmin_headers):
        """Test getting users with filters"""
        response = client.get("/api/superadmin/users?user_type=admin&is_active=true", headers=superadmin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_users_with_search(self, client, superadmin_headers):
        """Test searching users"""
        response = client.get("/api/superadmin/users?search=test", headers=superadmin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_user_by_id(self, client, test_user, superadmin_headers):
        """Test getting user by ID"""
        response = client.get(f"/api/superadmin/users/{test_user.id}", headers=superadmin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
    
    def test_get_user_by_id_not_found(self, client, superadmin_headers):
        """Test getting non-existent user"""
        fake_user_id = str(uuid.uuid4())
        response = client.get(f"/api/superadmin/users/{fake_user_id}", headers=superadmin_headers)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_create_user(self, client, superadmin_headers):
        """Test creating a new user"""
        user_data = {
            "email": "newadmin@example.com",
            "username": "newadmin",
            "full_name": "New Admin",
            "password": "newadminpass123",
            "user_type": "admin"
        }
        
        response = client.post("/api/superadmin/users", json=user_data, headers=superadmin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["full_name"] == user_data["full_name"]
        assert data["user_type"] == user_data["user_type"]
        assert data["is_active"] == True
        assert data["is_verified"] == True
    
    def test_create_user_duplicate_email(self, client, test_user, superadmin_headers):
        """Test creating user with duplicate email"""
        user_data = {
            "email": test_user.email,
            "username": "differentuser",
            "full_name": "Different User",
            "password": "pass123",
            "user_type": "user"
        }
        
        response = client.post("/api/superadmin/users", json=user_data, headers=superadmin_headers)
        assert response.status_code == 400
        assert "User with this email or username already exists" in response.json()["detail"]
    
    def test_update_user(self, client, test_user, superadmin_headers):
        """Test updating a user"""
        update_data = {
            "full_name": "Updated Full Name",
            "user_type": "admin"
        }
        
        response = client.put(f"/api/superadmin/users/{test_user.id}", json=update_data, headers=superadmin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["user_type"] == update_data["user_type"]
    
    def test_update_user_not_found(self, client, superadmin_headers):
        """Test updating non-existent user"""
        fake_user_id = str(uuid.uuid4())
        update_data = {
            "full_name": "Updated Name"
        }
        
        response = client.put(f"/api/superadmin/users/{fake_user_id}", json=update_data, headers=superadmin_headers)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_update_own_role_forbidden(self, client, test_superadmin, superadmin_headers):
        """Test that superadmin cannot change own role"""
        update_data = {
            "user_type": "admin"
        }
        
        response = client.put(f"/api/superadmin/users/{test_superadmin.id}", json=update_data, headers=superadmin_headers)
        assert response.status_code == 400
        assert "Cannot change your own role" in response.json()["detail"]
    
    def test_delete_user(self, client, test_user, superadmin_headers):
        """Test deleting a user"""
        response = client.delete(f"/api/superadmin/users/{test_user.id}", headers=superadmin_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "User deleted successfully"
    
    def test_delete_user_not_found(self, client, superadmin_headers):
        """Test deleting non-existent user"""
        fake_user_id = str(uuid.uuid4())
        response = client.delete(f"/api/superadmin/users/{fake_user_id}", headers=superadmin_headers)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_delete_own_account_forbidden(self, client, test_superadmin, superadmin_headers):
        """Test that superadmin cannot delete own account"""
        response = client.delete(f"/api/superadmin/users/{test_superadmin.id}", headers=superadmin_headers)
        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json()["detail"]

class TestSuperAdminRoleManagement:
    """Test super admin role management endpoints"""
    
    def test_promote_user_to_admin(self, client, test_user, superadmin_headers):
        """Test promoting user to admin"""
        response = client.post(f"/api/superadmin/users/{test_user.id}/promote", headers=superadmin_headers)
        assert response.status_code == 200
        assert f"User {test_user.username} promoted to admin" in response.json()["message"]
    
    def test_promote_user_not_found(self, client, superadmin_headers):
        """Test promoting non-existent user"""
        fake_user_id = str(uuid.uuid4())
        response = client.post(f"/api/superadmin/users/{fake_user_id}/promote", headers=superadmin_headers)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_promote_superadmin_forbidden(self, client, test_superadmin, superadmin_headers):
        """Test that superadmin cannot modify another superadmin role"""
        # Create another superadmin
        another_superadmin = User(
            id=str(uuid.uuid4()),
            email="another@example.com",
            username="anothersuperadmin",
            full_name="Another Superadmin",
            hashed_password="hashedpass",
            user_type="superadmin",
            is_active=True,
            is_verified=True
        )
        
        response = client.post(f"/api/superadmin/users/{another_superadmin.id}/promote", headers=superadmin_headers)
        assert response.status_code == 400
        assert "Cannot modify superadmin role" in response.json()["detail"]
    
    def test_demote_admin_to_user(self, client, test_admin, superadmin_headers):
        """Test demoting admin to user"""
        response = client.post(f"/api/superadmin/users/{test_admin.id}/demote", headers=superadmin_headers)
        assert response.status_code == 200
        assert f"Admin {test_admin.username} demoted to user" in response.json()["message"]
    
    def test_demote_user_not_found(self, client, superadmin_headers):
        """Test demoting non-existent user"""
        fake_user_id = str(uuid.uuid4())
        response = client.post(f"/api/superadmin/users/{fake_user_id}/demote", headers=superadmin_headers)
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_demote_superadmin_forbidden(self, client, test_superadmin, superadmin_headers):
        """Test that superadmin cannot demote another superadmin"""
        # Create another superadmin
        another_superadmin = User(
            id=str(uuid.uuid4()),
            email="another@example.com",
            username="anothersuperadmin",
            full_name="Another Superadmin",
            hashed_password="hashedpass",
            user_type="superadmin",
            is_active=True,
            is_verified=True
        )
        
        response = client.post(f"/api/superadmin/users/{another_superadmin.id}/demote", headers=superadmin_headers)
        assert response.status_code == 400
        assert "Cannot demote superadmin" in response.json()["detail"]
    
    def test_demote_self_forbidden(self, client, test_superadmin, superadmin_headers):
        """Test that superadmin cannot demote themselves"""
        response = client.post(f"/api/superadmin/users/{test_superadmin.id}/demote", headers=superadmin_headers)
        assert response.status_code == 400
        assert "Cannot demote yourself" in response.json()["detail"]

class TestSuperAdminAnalytics:
    """Test super admin analytics endpoints"""
    
    def test_get_advanced_analytics(self, client, superadmin_headers):
        """Test getting advanced analytics"""
        response = client.get("/api/superadmin/analytics/advanced", headers=superadmin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "user_stats" in data
        assert "content_stats" in data
        assert "review_stats" in data
        assert "recent_activity" in data
        
        # Check user stats structure
        user_stats = data["user_stats"]
        assert "total" in user_stats
        assert "active" in user_stats
        assert "verified" in user_stats
        assert "admins" in user_stats
        
        # Check content stats structure
        content_stats = data["content_stats"]
        assert "total_tools" in content_stats
        assert "featured_tools" in content_stats
        assert "total_blogs" in content_stats
        assert "published_blogs" in content_stats
        
        # Check review stats structure
        review_stats = data["review_stats"]
        assert "total" in review_stats
        assert "verified" in review_stats
        assert "average_rating" in review_stats

class TestSuperAdminToolAccessRequests:
    """Test super admin tool access request management"""
    
    def test_get_tool_access_requests(self, client, superadmin_headers):
        """Test getting all tool access requests"""
        response = client.get("/api/superadmin/tools/access-requests", headers=superadmin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_tool_access_requests_with_status_filter(self, client, superadmin_headers):
        """Test getting tool access requests with status filter"""
        response = client.get("/api/superadmin/tools/access-requests?status=pending", headers=superadmin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_update_tool_access_request_not_found(self, client, superadmin_headers):
        """Test updating non-existent access request"""
        fake_request_id = str(uuid.uuid4())
        update_data = {
            "status": "approved",
            "response_message": "Request approved"
        }
        
        response = client.put(f"/api/superadmin/tools/access-requests/{fake_request_id}", json=update_data, headers=superadmin_headers)
        assert response.status_code == 404
        assert "Access request not found" in response.json()["detail"]

class TestSuperAdminCategoryManagement:
    """Test super admin category management endpoints"""
    
    def test_create_category(self, client, superadmin_headers):
        """Test creating a new category"""
        category_data = {
            "name": "New Category",
            "description": "New category description",
            "icon": "new-icon",
            "color": "#00FF00"
        }
        
        response = client.post("/api/superadmin/categories", json=category_data, headers=superadmin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == category_data["name"]
        assert data["description"] == category_data["description"]
        assert data["icon"] == category_data["icon"]
        assert data["color"] == category_data["color"]
    
    def test_update_category(self, client, test_category, superadmin_headers):
        """Test updating a category"""
        update_data = {
            "name": "Updated Category Name",
            "description": "Updated description"
        }
        
        response = client.put(f"/api/superadmin/categories/{test_category.id}", json=update_data, headers=superadmin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["description"] == update_data["description"]
    
    def test_update_category_not_found(self, client, superadmin_headers):
        """Test updating non-existent category"""
        fake_category_id = str(uuid.uuid4())
        update_data = {
            "name": "Updated Name"
        }
        
        response = client.put(f"/api/superadmin/categories/{fake_category_id}", json=update_data, headers=superadmin_headers)
        assert response.status_code == 404
        assert "Category not found" in response.json()["detail"]
    
    def test_delete_category(self, client, test_category, superadmin_headers):
        """Test deleting a category"""
        response = client.delete(f"/api/superadmin/categories/{test_category.id}", headers=superadmin_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Category deleted successfully"
    
    def test_delete_category_not_found(self, client, superadmin_headers):
        """Test deleting non-existent category"""
        fake_category_id = str(uuid.uuid4())
        response = client.delete(f"/api/superadmin/categories/{fake_category_id}", headers=superadmin_headers)
        assert response.status_code == 404
        assert "Category not found" in response.json()["detail"]

class TestSuperAdminTrendingManagement:
    """Test super admin trending management endpoints"""
    
    def test_get_trending_stats(self, client, superadmin_headers):
        """Test getting trending statistics"""
        response = client.get("/api/superadmin/tools/trending-stats", headers=superadmin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_tools" in data
        assert "total_views" in data
        assert "avg_trending_score" in data
        assert "top_trending" in data
        assert isinstance(data["top_trending"], list)
    
    def test_download_sample_csv(self, client, superadmin_headers):
        """Test downloading sample CSV"""
        response = client.get("/api/superadmin/tools/sample-csv", headers=superadmin_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"

class TestSuperAdminAuth:
    """Test super admin authentication requirements"""
    
    def test_superadmin_required_endpoints(self, client, admin_headers):
        """Test that superadmin endpoints require superadmin role"""
        endpoints = [
            "/api/superadmin/users",
            "/api/superadmin/analytics/advanced",
            "/api/superadmin/tools/access-requests",
            "/api/superadmin/categories",
            "/api/superadmin/tools/trending-stats"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=admin_headers)
            assert response.status_code == 403
            assert "Not enough permissions" in response.json()["detail"]
    
    def test_unauthorized_access(self, client):
        """Test accessing superadmin endpoints without authentication"""
        endpoints = [
            "/api/superadmin/users",
            "/api/superadmin/analytics/advanced",
            "/api/superadmin/tools/access-requests"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401