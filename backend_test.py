import requests
import json
import time
import uuid
import random
import string
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Get backend URL from environment
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "http://localhost:8001")

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
    {"email": "admin@marketmindai.com", "password": "admin123", "type": "admin"}
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
    url = f"{BACKEND_URL}{endpoint}"
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
    else:
        print(f"✅ Status code {expected_status} as expected")
    
    return response

def test_health_check():
    """Test the health check endpoint"""
    print_test_header("Health Check")
    response = make_request("GET", "/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")
    return True

def test_login():
    """Test login endpoint with seeded users"""
    success = True
    for user in SEEDED_USERS:
        print_test_header(f"Login - {user['type'].capitalize()} User")
        login_data = {
            "email": user["email"],
            "password": user["password"]
        }
        response = make_request("POST", "/api/auth/login", login_data, expected_status=200)
        if response.status_code != 200:
            success = False
            continue
            
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
    if response.status_code != 401:
        success = False
    else:
        print("✅ Invalid credentials validation passed")
    
    return success

def test_tools_analytics():
    """Test tools analytics endpoint"""
    print_test_header("Tools Analytics")
    response = make_request("GET", "/api/tools/analytics")
    if response.status_code != 200:
        print("❌ Tools analytics endpoint failed")
        return False
    
    data = response.json()
    # Check if the response contains the expected data structure
    expected_keys = [
        "trending_tools", "top_rated_tools", "most_viewed_tools", 
        "newest_tools", "featured_tools", "hot_tools"
    ]
    
    for key in expected_keys:
        if key not in data:
            print(f"❌ Missing key in response: {key}")
            return False
        if not isinstance(data[key], list):
            print(f"❌ Expected list for {key}, got {type(data[key])}")
            return False
    
    print("✅ Tools analytics endpoint passed")
    return True

def test_advanced_search():
    """Test advanced search endpoint"""
    print_test_header("Advanced Search")
    
    # Test basic search
    response = make_request("GET", "/api/tools/search?page=1&per_page=10")
    if response.status_code != 200:
        print("❌ Basic search failed")
        return False
    
    # Test with filters
    filters = {
        "q": "tool",
        "category_id": "",
        "pricing_model": "Free",
        "sort_by": "rating"
    }
    
    query_params = "&".join([f"{k}={v}" for k, v in filters.items() if v])
    response = make_request("GET", f"/api/tools/search?{query_params}&page=1&per_page=10")
    if response.status_code != 200:
        print("❌ Advanced search with filters failed")
        return False
    
    # Check pagination
    data = response.json()
    expected_pagination_keys = ["total", "page", "per_page", "total_pages", "has_next", "has_prev"]
    for key in expected_pagination_keys:
        if key not in data:
            print(f"❌ Missing pagination key: {key}")
            return False
    
    print("✅ Advanced search endpoint passed")
    return True

def test_categories():
    """Test categories endpoint"""
    print_test_header("Categories")
    response = make_request("GET", "/api/categories")
    if response.status_code != 200:
        print("❌ Categories endpoint failed")
        return False
    
    # Check if we get a list of categories
    if not isinstance(response.json(), list):
        print("❌ Expected list of categories")
        return False
    
    print("✅ Categories endpoint passed")
    return True

def test_category_analytics():
    """Test category analytics endpoint"""
    print_test_header("Category Analytics")
    response = make_request("GET", "/api/categories/analytics")
    if response.status_code != 200:
        print("❌ Category analytics endpoint failed")
        return False
    
    # Check if we get a list of category analytics
    if not isinstance(response.json(), list):
        print("❌ Expected list of category analytics")
        return False
    
    print("✅ Category analytics endpoint passed")
    return True

def test_api_key_management():
    """Test API key management endpoint"""
    print_test_header("API Key Management")
    
    # Need to be logged in for this test
    if "admin" not in tokens:
        print("❌ Cannot test API key management without admin token")
        return False
    
    # Test updating API keys
    api_key_data = {
        "groq_api_key": "test_groq_key",
        "claude_api_key": "test_claude_key"
    }
    
    response = make_request(
        "PUT", 
        "/api/auth/api-keys", 
        data=api_key_data, 
        token=tokens["admin"],
        expected_status=200
    )
    
    if response.status_code != 200:
        print("❌ API key management endpoint failed")
        return False
    
    print("✅ API key management endpoint passed")
    return True

def test_user_profile():
    """Test user profile endpoint"""
    print_test_header("User Profile")
    
    # Need to be logged in for this test
    if "admin" not in tokens:
        print("❌ Cannot test user profile without admin token")
        return False
    
    response = make_request("GET", "/api/auth/me", token=tokens["admin"])
    if response.status_code != 200:
        print("❌ User profile endpoint failed")
        return False
    
    # Check if we get the user data
    user_data = response.json()
    expected_keys = ["id", "email", "username", "full_name", "user_type"]
    for key in expected_keys:
        if key not in user_data:
            print(f"❌ Missing user data key: {key}")
            return False
    
    print("✅ User profile endpoint passed")
    return True

def run_all_tests():
    """Run all tests"""
    results = {}
    
    try:
        # Basic health check
        results["health_check"] = test_health_check()
        
        # Authentication
        results["login"] = test_login()
        
        # Tools and categories
        results["tools_analytics"] = test_tools_analytics()
        results["advanced_search"] = test_advanced_search()
        results["categories"] = test_categories()
        results["category_analytics"] = test_category_analytics()
        
        # User features
        if "admin" in tokens:
            results["api_key_management"] = test_api_key_management()
            results["user_profile"] = test_user_profile()
        
        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        all_passed = True
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name}: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 All tests passed!")
        else:
            print("\n⚠️ Some tests failed!")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    run_all_tests()