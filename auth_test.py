#!/usr/bin/env python3
"""
Authentication Testing Script for MarketMindAI
Tests the specific authentication functionality requested in the review.
"""

import requests
import json
import uuid
import time
from typing import Dict, Any, Optional

# Get backend URL from frontend environment file
try:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.split('=', 1)[1].strip()
                break
        else:
            BACKEND_URL = "http://localhost:8001"
except:
    BACKEND_URL = "http://localhost:8001"

print(f"Testing authentication endpoints at: {BACKEND_URL}")

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
    expected_status: int = 200,
    files: Optional[Dict[str, Any]] = None
) -> requests.Response:
    """Make an HTTP request and validate the status code"""
    url = f"{BACKEND_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if method.lower() == "get":
        response = requests.get(url, headers=headers)
    elif method.lower() == "post":
        if files:
            response = requests.post(url, headers=headers, data=data, files=files)
        else:
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

def test_admin_login():
    """Test admin login with credentials from review request"""
    print_test_header("Admin Login Test")
    
    login_data = {
        "email": "admin@marketmindai.com",
        "password": "admin123"
    }
    
    response = make_request("POST", "/api/auth/login", login_data, expected_status=200)
    
    if response.status_code == 200:
        data = response.json()
        if "access_token" in data and "token_type" in data:
            print("✅ Admin login successful")
            print(f"✅ Token type: {data['token_type']}")
            return data["access_token"]
        else:
            print("❌ Login response missing required fields")
            return None
    else:
        print("❌ Admin login failed")
        return None

def test_get_current_user(token: str):
    """Test GET /api/auth/me endpoint"""
    print_test_header("Get Current User Info")
    
    response = make_request("GET", "/api/auth/me", token=token, expected_status=200)
    
    if response.status_code == 200:
        data = response.json()
        required_fields = ["id", "email", "username", "full_name", "user_type"]
        
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field: {field}")
                return False
        
        print("✅ Current user info retrieved successfully")
        print(f"✅ User type: {data['user_type']}")
        print(f"✅ Email: {data['email']}")
        return True
    else:
        print("❌ Failed to get current user info")
        return False

def test_user_registration():
    """Test POST /api/auth/register endpoint"""
    print_test_header("User Registration Test")
    
    # Generate unique user data
    unique_id = uuid.uuid4().hex[:8]
    user_data = {
        "email": f"testuser_{unique_id}@example.com",
        "username": f"testuser_{unique_id}",
        "full_name": "Test User Registration",
        "password": "TestPassword123!",
        "user_type": "user"
    }
    
    response = make_request("POST", "/api/auth/register", user_data, expected_status=200)
    
    if response.status_code == 200:
        data = response.json()
        required_fields = ["id", "email", "username", "full_name", "user_type"]
        
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field in registration response: {field}")
                return False
        
        print("✅ User registration successful")
        print(f"✅ Registered user ID: {data['id']}")
        print(f"✅ Registered email: {data['email']}")
        return True
    else:
        print("❌ User registration failed")
        return False

def test_email_verification():
    """Test POST /api/auth/verify-email endpoint"""
    print_test_header("Email Verification Test")
    
    # Test with invalid token (expected behavior)
    invalid_token_data = {
        "token": str(uuid.uuid4())
    }
    
    response = make_request("POST", "/api/auth/verify-email", invalid_token_data, expected_status=400)
    
    if response.status_code == 400:
        print("✅ Email verification correctly rejects invalid token")
        return True
    else:
        print("❌ Email verification should reject invalid token with 400")
        return False

def test_database_connection():
    """Test database connection by checking basic endpoints"""
    print_test_header("Database Connection Test")
    
    # Test health endpoint
    response = make_request("GET", "/api/health", expected_status=200)
    if response.status_code != 200:
        print("❌ Health check failed - database connection issue")
        return False
    
    # Test categories endpoint (requires database)
    response = make_request("GET", "/api/categories", expected_status=200)
    if response.status_code != 200:
        print("❌ Categories endpoint failed - database connection issue")
        return False
    
    # Test tools endpoint (requires database)
    response = make_request("GET", "/api/tools", expected_status=200)
    if response.status_code != 200:
        print("❌ Tools endpoint failed - database connection issue")
        return False
    
    print("✅ Database connection is working correctly")
    return True

def test_blog_endpoints(token: str):
    """Test blog endpoints"""
    print_test_header("Blog Endpoints Test")
    
    # Test GET /api/blogs
    response = make_request("GET", "/api/blogs", expected_status=200)
    if response.status_code != 200:
        print("❌ GET blogs endpoint failed")
        return False
    
    blogs = response.json()
    if not isinstance(blogs, list):
        print("❌ Blogs endpoint should return a list")
        return False
    
    print(f"✅ GET blogs successful - found {len(blogs)} blogs")
    
    # Test POST /api/blogs (create blog)
    # First get a category ID
    categories_response = make_request("GET", "/api/categories", expected_status=200)
    if categories_response.status_code != 200 or not categories_response.json():
        print("❌ Cannot get categories for blog creation test")
        return False
    
    category_id = categories_response.json()[0]["id"]
    
    blog_data = {
        "title": f"Test Blog {uuid.uuid4().hex[:8]}",
        "content": "This is a test blog content for authentication testing. " * 20,
        "excerpt": "Test blog excerpt",
        "status": "published",
        "category_id": category_id,
        "slug": f"test-blog-{uuid.uuid4().hex[:8]}"
    }
    
    response = make_request("POST", "/api/blogs", blog_data, token=token, expected_status=200)
    if response.status_code != 200:
        print("❌ POST blog creation failed")
        return False
    
    blog_id = response.json()["id"]
    print(f"✅ POST blog creation successful - created blog ID: {blog_id}")
    
    # Test GET /api/blogs/{id}
    response = make_request("GET", f"/api/blogs/{blog_id}", expected_status=200)
    if response.status_code != 200:
        print("❌ GET specific blog failed")
        return False
    
    print("✅ GET specific blog successful")
    print("✅ All blog endpoints working correctly")
    return True

def test_file_upload(token: str):
    """Test POST /api/upload endpoint"""
    print_test_header("File Upload Test")
    
    # Create a small test image (1x1 PNG)
    import base64
    png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU8j8wAAAABJRU5ErkJggg==")
    
    files = {'file': ('test.png', png_data, 'image/png')}
    
    response = make_request("POST", "/api/upload", files=files, token=token, expected_status=200)
    
    if response.status_code == 200:
        data = response.json()
        required_fields = ["file_url", "filename", "content_type", "size"]
        
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field in upload response: {field}")
                return False
        
        if not data["file_url"].startswith("data:image/png;base64,"):
            print("❌ File upload should return data URL")
            return False
        
        print("✅ File upload successful")
        print(f"✅ Uploaded file: {data['filename']}")
        print(f"✅ Content type: {data['content_type']}")
        print(f"✅ File size: {data['size']} bytes")
        return True
    else:
        print("❌ File upload failed")
        return False

def main():
    """Run all authentication tests"""
    print("=" * 80)
    print("MARKETMINDAI AUTHENTICATION TESTING")
    print("=" * 80)
    
    results = {}
    
    # Test 1: Admin Login
    admin_token = test_admin_login()
    results["admin_login"] = admin_token is not None
    
    if admin_token:
        # Test 2: Get Current User
        results["get_current_user"] = test_get_current_user(admin_token)
        
        # Test 6: Blog Endpoints
        results["blog_endpoints"] = test_blog_endpoints(admin_token)
        
        # Test 7: File Upload
        results["file_upload"] = test_file_upload(admin_token)
    else:
        results["get_current_user"] = False
        results["blog_endpoints"] = False
        results["file_upload"] = False
    
    # Test 3: User Registration
    results["user_registration"] = test_user_registration()
    
    # Test 4: Email Verification
    results["email_verification"] = test_email_verification()
    
    # Test 5: Database Connection
    results["database_connection"] = test_database_connection()
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL AUTHENTICATION TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total_tests - passed_tests} TEST(S) FAILED")
        return False

if __name__ == "__main__":
    main()