import pytest
from fastapi.testclient import TestClient
from models import User

class TestUserAuthentication:
    """Test user authentication endpoints"""
    
    def test_register_user_success(self, client, db):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "newpass123",
            "user_type": "user"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["full_name"] == user_data["full_name"]
        assert data["user_type"] == user_data["user_type"]
        assert data["is_verified"] == False
        
        # Check user exists in database
        db_user = db.query(User).filter(User.email == user_data["email"]).first()
        assert db_user is not None
        assert db_user.username == user_data["username"]
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email"""
        user_data = {
            "email": test_user.email,
            "username": "differentuser",
            "full_name": "Different User",
            "password": "pass123",
            "user_type": "user"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username"""
        user_data = {
            "email": "different@example.com",
            "username": test_user.username,
            "full_name": "Different User",
            "password": "pass123",
            "user_type": "user"
        }
        
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]
    
    def test_login_success(self, client, test_user):
        """Test successful login"""
        login_data = {
            "email": test_user.email,
            "password": "testpass123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password"""
        login_data = {
            "email": test_user.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_get_current_user(self, client, test_user, auth_headers):
        """Test getting current user info"""
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["username"] == test_user.username
        assert data["full_name"] == test_user.full_name
    
    def test_get_current_user_unauthorized(self, client):
        """Test getting current user without authentication"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

class TestUserProfile:
    """Test user profile management endpoints"""
    
    def test_update_api_keys(self, client, test_user, auth_headers):
        """Test updating user API keys"""
        update_data = {
            "groq_api_key": "test_groq_key",
            "claude_api_key": "test_claude_key"
        }
        
        response = client.put("/api/user/api-keys", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "API keys updated successfully"
    
    def test_update_profile(self, client, test_user, auth_headers):
        """Test updating user profile"""
        update_data = {
            "full_name": "Updated Name"
        }
        
        response = client.put("/api/user/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["message"] == "Profile updated successfully"
    
    def test_get_dashboard_stats(self, client, test_user, auth_headers):
        """Test getting user dashboard statistics"""
        response = client.get("/api/user/dashboard-stats", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "content_stats" in data
        assert "recent_activity" in data
        assert "blogs" in data["content_stats"]
        assert "reviews" in data["content_stats"]
        assert "comments" in data["content_stats"]
        assert "ai_content" in data["content_stats"]

class TestAIContent:
    """Test AI content generation endpoints"""
    
    def test_generate_ai_content_unauthorized(self, client):
        """Test AI content generation without authentication"""
        content_request = {
            "prompt": "Generate a blog post about AI",
            "content_type": "blog",
            "provider": "groq"
        }
        
        response = client.post("/api/user/ai/generate-content", json=content_request)
        assert response.status_code == 401
    
    def test_get_ai_content_history(self, client, test_user, auth_headers):
        """Test getting AI content history"""
        response = client.get("/api/user/ai/content-history", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)