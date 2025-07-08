import requests
import json
import time
import uuid
import random
import string
from typing import Dict, Any, Optional

# Backend URL
BASE_URL = "http://localhost:8001"

# Test data
TEST_USER = {
    "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
    "username": f"testuser_{uuid.uuid4().hex[:8]}",
    "full_name": "Test User",
    "password": "TestPassword123!",
    "user_type": "user"
}

# Seeded users for testing
SEEDED_USERS = [
    {"email": "user@marketmindai.com", "password": "password123", "type": "user"},
    {"email": "admin@marketmindai.com", "password": "admin123", "type": "admin"},
    {"email": "superadmin@marketmindai.com", "password": "superadmin123", "type": "superadmin"}
]

# Store tokens and verification tokens
tokens = {}
verification_token = None

def print_test_header(test_name: str) -> None:
    """Print a formatted test header"""
    print("\n" + "=" * 80)
    print(f"TEST: {test_name}")
    print("=" * 80)

def print_response(response: requests.Response) -> None:
    """Print response details"""
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    expected_status: int = 200
) -> requests.Response:
    """Make an HTTP request and validate the status code"""
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if method.lower() == "get":
        response = requests.get(url, headers=headers)
    elif method.lower() == "post":
        response = requests.post(url, json=data, headers=headers)
    elif method.lower() == "put":
        response = requests.put(url, json=data, headers=headers)
    elif method.lower() == "delete":
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    print_response(response)
    
    if response.status_code != expected_status:
        print(f"❌ Expected status code {expected_status}, got {response.status_code}")
        return response
    
    print(f"✅ Status code {expected_status} as expected")
    return response

def test_health_check():
    """Test the health check endpoint"""
    print_test_header("Health Check")
    response = make_request("GET", "/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")

def test_user_registration():
    """Test user registration endpoint"""
    global verification_token
    
    print_test_header("User Registration - Valid Data")
    response = make_request("POST", "/api/auth/register", TEST_USER, expected_status=200)
    assert response.status_code == 200
    
    # Extract verification token from response (in a real scenario, this would be sent via email)
    # For testing purposes, we'll assume the token is in the response or extract it from the database
    # Since we can't access the database directly in this test, we'll check if the response contains user data
    assert "id" in response.json()
    assert response.json()["email"] == TEST_USER["email"]
    assert response.json()["username"] == TEST_USER["username"]
    assert response.json()["is_verified"] == False
    
    # In a real scenario, we would extract the verification token from the email or database
    # For this test, we'll need to check the server logs or database to get the token
    # Let's assume we have a way to get it (in this case, we'll use a placeholder)
    verification_token = "placeholder_token"  # This would be extracted from email or database
    
    print("✅ User registration with valid data passed")
    
    # Test duplicate email
    print_test_header("User Registration - Duplicate Email")
    duplicate_user = TEST_USER.copy()
    duplicate_user["username"] = f"different_user_{uuid.uuid4().hex[:8]}"
    response = make_request("POST", "/api/auth/register", duplicate_user, expected_status=400)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]
    print("✅ Duplicate email validation passed")
    
    # Test duplicate username
    print_test_header("User Registration - Duplicate Username")
    duplicate_user = TEST_USER.copy()
    duplicate_user["email"] = f"different_{uuid.uuid4().hex[:8]}@example.com"
    response = make_request("POST", "/api/auth/register", duplicate_user, expected_status=400)
    assert response.status_code == 400
    assert "Username already taken" in response.json()["detail"]
    print("✅ Duplicate username validation passed")

def test_login():
    """Test login endpoint with seeded users"""
    for user in SEEDED_USERS:
        print_test_header(f"Login - {user['type'].capitalize()} User")
        login_data = {
            "email": user["email"],
            "password": user["password"]
        }
        response = make_request("POST", "/api/auth/login", login_data, expected_status=200)
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"
        
        # Store token for later use
        tokens[user["type"]] = response.json()["access_token"]
        print(f"✅ Login as {user['type']} passed")
    
    # Test invalid credentials
    print_test_header("Login - Invalid Credentials")
    login_data = {
        "email": "user@marketmindai.com",
        "password": "wrongpassword"
    }
    response = make_request("POST", "/api/auth/login", login_data, expected_status=401)
    assert response.status_code == 401
    print("✅ Invalid credentials validation passed")
    
    # Test login with unverified user
    # Since we can't directly test this without having a verified token,
    # we'll just check that the endpoint exists and returns the expected error
    print_test_header("Login - Unverified User")
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    response = make_request("POST", "/api/auth/login", login_data, expected_status=400)
    assert response.status_code == 400
    assert "Email not verified" in response.json()["detail"]
    print("✅ Unverified user validation passed")

def test_email_verification():
    """Test email verification endpoint"""
    # Since we don't have a real verification token, we'll test with invalid token
    print_test_header("Email Verification - Invalid Token")
    verification_data = {
        "token": "invalid_token"
    }
    response = make_request("POST", "/api/auth/verify-email", verification_data, expected_status=400)
    assert response.status_code == 400
    assert "Invalid or expired verification token" in response.json()["detail"]
    print("✅ Invalid verification token validation passed")
    
    # For a valid token test, we would need the actual token from the database
    # In a real scenario, this would be extracted from the email or database
    # For this test, we'll skip the valid token test

def test_password_reset():
    """Test password reset flow"""
    # Request password reset
    print_test_header("Password Reset - Request")
    reset_request_data = {
        "email": SEEDED_USERS[0]["email"]
    }
    response = make_request("POST", "/api/auth/request-password-reset", reset_request_data, expected_status=200)
    assert response.status_code == 200
    assert "message" in response.json()
    print("✅ Password reset request passed")
    
    # Test reset password with invalid token
    print_test_header("Password Reset - Invalid Token")
    reset_data = {
        "token": "invalid_token",
        "new_password": "NewPassword123!"
    }
    response = make_request("POST", "/api/auth/reset-password", reset_data, expected_status=400)
    assert response.status_code == 400
    assert "Invalid or expired reset token" in response.json()["detail"]
    print("✅ Invalid reset token validation passed")
    
    # For a valid token test, we would need the actual token from the database
    # In a real scenario, this would be extracted from the email or database
    # For this test, we'll skip the valid token test

def test_protected_routes():
    """Test protected routes with different user types"""
    # Test accessing user profile without token
    print_test_header("Protected Routes - User Profile Without Token")
    response = make_request("GET", "/api/auth/me", expected_status=401)
    assert response.status_code == 401
    print("✅ Accessing user profile without token validation passed")
    
    # Test accessing user profile with token
    print_test_header("Protected Routes - User Profile With Token")
    response = make_request("GET", "/api/auth/me", token=tokens["user"], expected_status=200)
    assert response.status_code == 200
    assert "id" in response.json()
    assert "email" in response.json()
    print("✅ Accessing user profile with token passed")
    
    # Test admin-only route with user token
    print_test_header("Protected Routes - Admin Route With User Token")
    response = make_request("GET", "/api/users", token=tokens["user"], expected_status=403)
    assert response.status_code == 403
    print("✅ Accessing admin route with user token validation passed")
    
    # Test admin-only route with admin token
    print_test_header("Protected Routes - Admin Route With Admin Token")
    response = make_request("GET", "/api/users", token=tokens["admin"], expected_status=200)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    print("✅ Accessing admin route with admin token passed")
    
    # Test superadmin-only route with admin token
    print_test_header("Protected Routes - SuperAdmin Route With Admin Token")
    # Find a user ID to delete
    users_response = make_request("GET", "/api/users", token=tokens["admin"], expected_status=200)
    if users_response.json() and len(users_response.json()) > 0:
        user_id = users_response.json()[0]["id"]
        response = make_request("DELETE", f"/api/users/{user_id}", token=tokens["admin"], expected_status=403)
        assert response.status_code == 403
        print("✅ Accessing superadmin route with admin token validation passed")
    else:
        print("⚠️ No users found to test superadmin route")

def test_categories_and_tools_api():
    """Test categories and tools API endpoints"""
    # Test get categories
    print_test_header("Categories API - Get Categories")
    response = make_request("GET", "/api/categories", expected_status=200)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    print("✅ Get categories passed")
    
    # Test get tools
    print_test_header("Tools API - Get Tools")
    response = make_request("GET", "/api/tools", expected_status=200)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    print("✅ Get tools passed")
    
    # Test get blogs
    print_test_header("Blogs API - Get Blogs")
    response = make_request("GET", "/api/blogs", expected_status=200)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    print("✅ Get blogs passed")

def run_all_tests():
    """Run all tests"""
    try:
        test_health_check()
        test_user_registration()
        test_login()
        test_email_verification()
        test_password_reset()
        test_protected_routes()
        test_categories_and_tools_api()
        
        print("\n" + "=" * 80)
        print("🎉 All tests completed!")
        print("=" * 80)
    except AssertionError as e:
        print(f"\n❌ Test failed: {str(e)}")
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    run_all_tests()