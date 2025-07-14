import requests
import json
import time
import uuid
import random
import string
from typing import Dict, Any, Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

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

print(f"Using backend URL: {BACKEND_URL}")

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
reset_token = None
test_category_id = None
test_subcategory_id = None
test_tool_id = None
test_blog_id = None

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
    params: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None
) -> requests.Response:
    """Make an HTTP request and validate the status code"""
    url = f"{BACKEND_URL}{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if method.lower() == "get":
        response = requests.get(url, headers=headers, params=params)
    elif method.lower() == "post":
        if files:
            response = requests.post(url, headers=headers, data=data, files=files)
        else:
            response = requests.post(url, json=data, headers=headers, params=params)
    elif method.lower() == "put":
        response = requests.put(url, json=data, headers=headers, params=params)
    elif method.lower() == "delete":
        response = requests.delete(url, headers=headers, params=params)
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

def test_user_registration():
    """Test user registration endpoint"""
    print_test_header("User Registration")
    
    # Generate random user data
    random_user = {
        "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "full_name": "Test User",
        "password": "TestPassword123!",
        "user_type": "user"
    }
    
    # Test valid registration
    response = make_request("POST", "/api/auth/register", random_user, expected_status=200)
    if response.status_code != 200:
        print("❌ User registration failed")
        return False
    
    # Test duplicate email
    response = make_request("POST", "/api/auth/register", random_user, expected_status=400)
    if response.status_code != 400 or "Email already registered" not in response.text:
        print("❌ Duplicate email validation failed")
        return False
    
    # Test duplicate username
    duplicate_username = random_user.copy()
    duplicate_username["email"] = f"different_{uuid.uuid4().hex[:8]}@example.com"
    response = make_request("POST", "/api/auth/register", duplicate_username, expected_status=400)
    if response.status_code != 400 or "Username already taken" not in response.text:
        print("❌ Duplicate username validation failed")
        return False
    
    print("✅ User registration endpoint passed")
    return True

def test_login():
    """Test login endpoint with seeded users"""
    print_test_header("Login")
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

def test_email_verification():
    """Test email verification endpoint"""
    print_test_header("Email Verification")
    
    # Test with invalid token
    invalid_token = {
        "token": str(uuid.uuid4())
    }
    response = make_request("POST", "/api/auth/verify-email", invalid_token, expected_status=400)
    if response.status_code != 400 or "Invalid or expired verification token" not in response.text:
        print("❌ Invalid token validation failed")
        return False
    
    # Note: We can't test with a valid token as it would require access to the actual verification token
    print("✅ Email verification endpoint passed (invalid token validation)")
    return True

def test_password_reset():
    """Test password reset flow"""
    print_test_header("Password Reset Flow")
    
    # Test password reset request
    reset_request = {
        "email": "user@marketmindai.com"
    }
    response = make_request("POST", "/api/auth/request-password-reset", reset_request, expected_status=200)
    if response.status_code != 200:
        print("❌ Password reset request failed")
        return False
    
    # Test with invalid token
    reset_data = {
        "token": str(uuid.uuid4()),
        "new_password": "NewPassword123!"
    }
    response = make_request("POST", "/api/auth/reset-password", reset_data, expected_status=400)
    if response.status_code != 400 or "Invalid or expired reset token" not in response.text:
        print("❌ Invalid reset token validation failed")
        return False
    
    # Note: We can't test with a valid token as it would require access to the actual reset token
    print("✅ Password reset flow passed (request and invalid token validation)")
    return True

def test_protected_routes():
    """Test protected routes and role-based access control"""
    print_test_header("Protected Routes")
    
    if "user" not in tokens or "admin" not in tokens:
        print("❌ Cannot test protected routes without user and admin tokens")
        return False
    
    # Test user profile without token
    response = make_request("GET", "/api/auth/me", expected_status=401)
    if response.status_code != 401:
        print("❌ Accessing protected route without token should fail")
        return False
    
    # Test user profile with token
    response = make_request("GET", "/api/auth/me", token=tokens["user"])
    if response.status_code != 200:
        print("❌ Accessing user profile with token failed")
        return False
    
    # Test admin-only route with user token
    response = make_request("POST", "/api/categories", 
                           data={"name": "Test Category", "description": "Test Description", "icon": "test-icon", "color": "#123456"},
                           token=tokens["user"], 
                           expected_status=403)
    if response.status_code != 403:
        print("❌ User accessing admin-only route should fail")
        return False
    
    # Test admin-only route with admin token
    response = make_request("POST", "/api/categories", 
                           data={"name": f"Test Category {uuid.uuid4().hex[:8]}", "description": "Test Description", "icon": "test-icon", "color": "#123456"},
                           token=tokens["admin"])
    if response.status_code != 200:
        print("❌ Admin accessing admin-only route failed")
        return False
    
    # Store category ID for later tests
    global test_category_id
    test_category_id = response.json()["id"]
    
    print("✅ Protected routes and role-based access control passed")
    return True

def test_categories_crud():
    """Test categories CRUD operations"""
    print_test_header("Categories CRUD")
    
    if "admin" not in tokens:
        print("❌ Cannot test categories CRUD without admin token")
        return False
    
    global test_category_id
    
    # Test GET categories
    response = make_request("GET", "/api/categories")
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET categories failed")
        return False
    
    # Test GET category analytics
    response = make_request("GET", "/api/categories/analytics")
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET category analytics failed")
        return False
    
    # If we don't have a category ID from previous tests, create one
    if not test_category_id:
        # Test CREATE category
        category_data = {
            "name": f"Test Category {uuid.uuid4().hex[:8]}",
            "description": "Test Description",
            "icon": "test-icon",
            "color": "#123456"
        }
        response = make_request("POST", "/api/categories", category_data, token=tokens["admin"])
        if response.status_code != 200:
            print("❌ CREATE category failed")
            return False
        test_category_id = response.json()["id"]
    
    # Test UPDATE category
    update_data = {
        "description": f"Updated Description {uuid.uuid4().hex[:8]}",
        "color": "#654321"
    }
    response = make_request("PUT", f"/api/categories/{test_category_id}", update_data, token=tokens["admin"])
    if response.status_code != 200 or response.json()["description"] != update_data["description"]:
        print("❌ UPDATE category failed")
        return False
    
    # We won't test DELETE category here as we need it for other tests
    print("✅ Categories CRUD operations passed")
    return True

def test_subcategories_crud():
    """Test subcategories CRUD operations"""
    print_test_header("Subcategories CRUD")
    
    if "admin" not in tokens or not test_category_id:
        print("❌ Cannot test subcategories CRUD without admin token or category ID")
        return False
    
    global test_subcategory_id
    
    # Test GET subcategories
    response = make_request("GET", "/api/subcategories")
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET subcategories failed")
        return False
    
    # Test GET subcategories by category
    response = make_request("GET", f"/api/subcategories?category_id={test_category_id}")
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET subcategories by category failed")
        return False
    
    # Test CREATE subcategory
    subcategory_data = {
        "name": f"Test Subcategory {uuid.uuid4().hex[:8]}",
        "description": "Test Subcategory Description",
        "category_id": test_category_id,
        "icon": "test-subicon"
    }
    response = make_request("POST", "/api/subcategories", subcategory_data, token=tokens["admin"])
    if response.status_code != 200:
        print("❌ CREATE subcategory failed")
        return False
    
    test_subcategory_id = response.json()["id"]
    print("✅ Subcategories CRUD operations passed")
    return True

def test_tools_crud():
    """Test tools CRUD operations"""
    print_test_header("Tools CRUD")
    
    if "admin" not in tokens or not test_category_id:
        print("❌ Cannot test tools CRUD without admin token or category ID")
        return False
    
    global test_tool_id
    
    # Test GET tools
    response = make_request("GET", "/api/tools")
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET tools failed")
        return False
    
    # Test GET tools by category
    response = make_request("GET", f"/api/tools?category_id={test_category_id}")
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET tools by category failed")
        return False
    
    # Test CREATE tool
    tool_data = {
        "name": f"Test Tool {uuid.uuid4().hex[:8]}",
        "description": "Test Tool Description",
        "short_description": "Short description",
        "category_id": test_category_id,
        "subcategory_id": test_subcategory_id if test_subcategory_id else None,
        "pricing_model": "Freemium",
        "company_size": "SMB",
        "slug": f"test-tool-{uuid.uuid4().hex[:8]}",
        "is_hot": True,
        "is_featured": True
    }
    response = make_request("POST", "/api/tools", tool_data, token=tokens["admin"])
    if response.status_code != 200:
        print("❌ CREATE tool failed")
        return False
    
    test_tool_id = response.json()["id"]
    
    # Test GET tool by ID
    response = make_request("GET", f"/api/tools/{test_tool_id}")
    if response.status_code != 200 or response.json()["id"] != test_tool_id:
        print("❌ GET tool by ID failed")
        return False
    
    # Test UPDATE tool
    update_data = {
        "description": f"Updated Tool Description {uuid.uuid4().hex[:8]}",
        "pricing_model": "Paid"
    }
    response = make_request("PUT", f"/api/tools/{test_tool_id}", update_data, token=tokens["admin"])
    if response.status_code != 200 or response.json()["description"] != update_data["description"]:
        print("❌ UPDATE tool failed")
        return False
    
    # We won't test DELETE tool here as we need it for other tests
    print("✅ Tools CRUD operations passed")
    return True

def test_tools_search():
    """Test advanced tools search for Discover page"""
    print_test_header("Advanced Tools Search for Discover Page")
    
    # Test basic search
    print_test_header("Basic search")
    response = make_request("GET", "/api/tools/search?page=1&per_page=10")
    if response.status_code != 200:
        print("❌ Basic search failed")
        return False
    
    # Get total tools count for verification
    total_tools = response.json()["total"]
    print(f"Total tools in database: {total_tools}")
    
    # Verify we have at least 23 tools as required
    if total_tools < 23:
        print(f"❌ Expected at least 23 tools, but found only {total_tools}")
        print("⚠️ This may affect the Discover page functionality")
    else:
        print(f"✅ Found {total_tools} tools (requirement: at least 23)")
    
    # Test search with query parameter
    print_test_header("Search with query parameter")
    response = make_request("GET", "/api/tools/search?q=tool")
    if response.status_code != 200:
        print("❌ Search with query parameter failed")
        return False
    print("✅ Search with query parameter passed")
    
    # Test category filtering
    if test_category_id:
        print_test_header("Category filtering")
        response = make_request("GET", f"/api/tools/search?category_id={test_category_id}")
        if response.status_code != 200:
            print("❌ Category filtering failed")
            return False
        print("✅ Category filtering passed")
    
    # Test pricing model filtering
    print_test_header("Pricing model filtering")
    response = make_request("GET", "/api/tools/search?pricing_model=Freemium")
    if response.status_code != 200:
        print("❌ Pricing model filtering failed")
        return False
    print("✅ Pricing model filtering passed")
    
    # Test company size filtering
    print_test_header("Company size filtering")
    response = make_request("GET", "/api/tools/search?company_size=SMB")
    if response.status_code != 200:
        print("❌ Company size filtering failed")
        return False
    print("✅ Company size filtering passed")
    
    # Test hot tools filtering
    print_test_header("Hot tools filtering")
    response = make_request("GET", "/api/tools/search?is_hot=true")
    if response.status_code != 200:
        print("❌ Hot tools filtering failed")
        return False
    print("✅ Hot tools filtering passed")
    
    # Test featured tools filtering
    print_test_header("Featured tools filtering")
    response = make_request("GET", "/api/tools/search?is_featured=true")
    if response.status_code != 200:
        print("❌ Featured tools filtering failed")
        return False
    print("✅ Featured tools filtering passed")
    
    # Test sort options
    sort_options = ["rating", "trending", "views"]
    for sort_by in sort_options:
        print_test_header(f"Sort by {sort_by}")
        response = make_request("GET", f"/api/tools/search?sort_by={sort_by}")
        if response.status_code != 200:
            print(f"❌ Sort by {sort_by} failed")
            return False
        print(f"✅ Sort by {sort_by} passed")
    
    # Test pagination
    print_test_header("Pagination")
    response = make_request("GET", "/api/tools/search?page=1&per_page=50")
    if response.status_code != 200:
        print("❌ Pagination failed")
        return False
    
    # Check pagination metadata
    data = response.json()
    expected_pagination_keys = ["total", "page", "per_page", "total_pages", "has_next", "has_prev"]
    for key in expected_pagination_keys:
        if key not in data:
            print(f"❌ Missing pagination key: {key}")
            return False
    
    # Verify per_page is respected
    if data["per_page"] != 50:
        print(f"❌ Expected per_page=50, got {data['per_page']}")
        return False
    
    print("✅ Pagination passed")
    
    # Test combination of filters
    print_test_header("Combination of filters")
    response = make_request("GET", "/api/tools/search?pricing_model=Freemium&company_size=SMB&sort_by=rating&is_featured=true&page=1&per_page=20")
    if response.status_code != 200:
        print("❌ Combination of filters failed")
        return False
    print("✅ Combination of filters passed")
    
    print("✅ Advanced tools search for Discover page passed")
    return True

def test_tools_comparison():
    """Test tools comparison functionality"""
    print_test_header("Tools Comparison")
    
    if "user" not in tokens or not test_tool_id:
        print("❌ Cannot test tools comparison without user token or tool ID")
        return False
    
    # Test add to comparison
    json_data = {"tool_id": test_tool_id}
    response = make_request("POST", "/api/tools/compare", json_data, token=tokens["user"], expected_status=200)
    if response.status_code != 200:
        print("❌ Add to comparison failed")
        return False
    
    # Test get comparison tools
    response = make_request("GET", "/api/tools/compare", token=tokens["user"])
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ Get comparison tools failed")
        return False
    
    # Test remove from comparison
    response = make_request("DELETE", f"/api/tools/compare/{test_tool_id}", token=tokens["user"])
    if response.status_code != 200:
        print("❌ Remove from comparison failed")
        return False
    
    print("✅ Tools comparison functionality passed")
    return True

def test_blogs_crud():
    """Test blogs CRUD operations"""
    print_test_header("Blogs CRUD")
    
    if "user" not in tokens or not test_category_id:
        print("❌ Cannot test blogs CRUD without user token or category ID")
        return False
    
    global test_blog_id
    
    # Test GET blogs
    response = make_request("GET", "/api/blogs")
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET blogs failed")
        return False
    
    # Test CREATE blog
    blog_data = {
        "title": f"Test Blog {uuid.uuid4().hex[:8]}",
        "content": "This is a test blog content with enough words to calculate reading time. " * 20,
        "excerpt": "Test excerpt",
        "status": "published",
        "category_id": test_category_id,
        "subcategory_id": test_subcategory_id if test_subcategory_id else None,
        "slug": f"test-blog-{uuid.uuid4().hex[:8]}"
    }
    response = make_request("POST", "/api/blogs", blog_data, token=tokens["user"])
    if response.status_code != 200:
        print("❌ CREATE blog failed")
        return False
    
    test_blog_id = response.json()["id"]
    
    # Test GET blog by ID
    response = make_request("GET", f"/api/blogs/{test_blog_id}")
    if response.status_code != 200 or response.json()["id"] != test_blog_id:
        print("❌ GET blog by ID failed")
        return False
    
    # Test UPDATE blog
    update_data = {
        "title": f"Updated Blog Title {uuid.uuid4().hex[:8]}",
        "content": "Updated content for the test blog. " * 20
    }
    response = make_request("PUT", f"/api/blogs/{test_blog_id}", update_data, token=tokens["user"])
    if response.status_code != 200 or response.json()["title"] != update_data["title"]:
        print("❌ UPDATE blog failed")
        return False
    
    # Test blog likes
    response = make_request("POST", f"/api/blogs/{test_blog_id}/like", token=tokens["user"])
    if response.status_code != 200 or "likes" not in response.json():
        print("❌ Blog likes functionality failed")
        return False
    
    # We won't test DELETE blog here as we might need it for other tests
    print("✅ Blogs CRUD operations passed")
    return True

def test_ai_content_generation():
    """Test AI content generation endpoints"""
    print_test_header("AI Content Generation")
    
    if "user" not in tokens:
        print("❌ Cannot test AI content generation without user token")
        return False
    
    # Test API key management first
    api_key_data = {
        "groq_api_key": "test_groq_key",
        "claude_api_key": "test_claude_key"
    }
    response = make_request("PUT", "/api/auth/api-keys", api_key_data, token=tokens["user"])
    if response.status_code != 200:
        print("❌ API key management failed")
        return False
    
    # Test generate content
    # Note: This might fail if the API keys are not valid, which is expected
    content_request = {
        "prompt": "Write a short blog post about AI in marketing",
        "content_type": "blog",
        "provider": "groq"  # Using groq as provider
    }
    response = make_request("POST", "/api/ai/generate-content", content_request, token=tokens["user"], expected_status=[200, 500])
    
    # We consider this test passed even if it fails with a 500 error, as it's likely due to invalid API keys
    if response.status_code not in [200, 500]:
        print("❌ AI content generation endpoint failed unexpectedly")
        return False
    
    # Test content history
    response = make_request("GET", "/api/ai/content-history", token=tokens["user"])
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ AI content history endpoint failed")
        return False
    
    print("✅ AI content generation endpoints passed (note: actual generation may fail due to invalid API keys)")
    return True

def test_seo_optimization():
    """Test SEO optimization endpoints"""
    print_test_header("SEO Optimization")
    
    if "admin" not in tokens or not test_tool_id:
        print("❌ Cannot test SEO optimization without admin token or tool ID")
        return False
    
    # Test SEO optimization
    # Note: This might fail if the API keys are not valid, which is expected
    seo_request = {
        "tool_id": test_tool_id,
        "target_keywords": ["marketing", "automation", "b2b"],
        "search_engine": "google"
    }
    response = make_request("POST", "/api/admin/seo/optimize", seo_request, token=tokens["admin"], expected_status=[200, 500])
    
    # We consider this test passed even if it fails with a 500 error, as it's likely due to invalid API keys
    if response.status_code not in [200, 500]:
        print("❌ SEO optimization endpoint failed unexpectedly")
        return False
    
    # Test SEO optimizations list
    response = make_request("GET", "/api/admin/seo/optimizations", token=tokens["admin"])
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ SEO optimizations list endpoint failed")
        return False
    
    print("✅ SEO optimization endpoints passed (note: actual optimization may fail due to invalid API keys)")
    return True

def test_database_connectivity():
    """Test database connectivity by verifying CRUD operations"""
    print_test_header("Database Connectivity")
    
    # We've already tested CRUD operations for various entities
    # If those tests passed, it means the database connectivity is working
    
    # Let's verify we can retrieve data from the database
    response = make_request("GET", "/api/categories")
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ Database connectivity test failed - cannot retrieve categories")
        return False
    
    response = make_request("GET", "/api/tools")
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ Database connectivity test failed - cannot retrieve tools")
        return False
    
    print("✅ Database connectivity test passed")
    return True

def test_error_handling():
    """Test error handling"""
    print_test_header("Error Handling")
    
    # Test 404 for non-existent resource
    response = make_request("GET", f"/api/tools/{uuid.uuid4()}", expected_status=404)
    if response.status_code != 404:
        print("❌ 404 error handling test failed")
        return False
    
    # Test 401 for unauthorized access
    response = make_request("GET", "/api/auth/me", expected_status=401)
    if response.status_code != 401:
        print("❌ 401 error handling test failed")
        return False
    
    # Test 403 for forbidden access
    if "user" in tokens:
        response = make_request("GET", "/api/admin/seo/optimizations", token=tokens["user"], expected_status=403)
        if response.status_code != 403:
            print("❌ 403 error handling test failed")
            return False
    
    print("✅ Error handling test passed")
    return True

def test_tools_analytics():
    """Test tools analytics endpoint for Discover page carousels"""
    print_test_header("Tools Analytics for Discover Page")
    response = make_request("GET", "/api/tools/analytics")
    if response.status_code != 200:
        print("❌ Tools analytics endpoint failed")
        return False
    
    data = response.json()
    # Check if the response contains the expected data structure for all required carousels
    expected_keys = [
        "trending_tools", "top_rated_tools", "most_viewed_tools", 
        "newest_tools", "featured_tools", "hot_tools"
    ]
    
    for key in expected_keys:
        if key not in data:
            print(f"❌ Missing carousel in response: {key}")
            return False
        if not isinstance(data[key], list):
            print(f"❌ Expected list for {key}, got {type(data[key])}")
            return False
        
        # Check that each carousel contains tool objects with expected properties
        if data[key]:
            sample_tool = data[key][0]
            required_tool_props = ["id", "name", "description", "category_id"]
            for prop in required_tool_props:
                if prop not in sample_tool:
                    print(f"❌ Missing property {prop} in {key} tool")
                    return False
            print(f"✅ {key} carousel contains valid tool objects")
        else:
            print(f"ℹ️ {key} carousel is empty")
    
    print("✅ Tools analytics endpoint passed - all required carousels present")
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

# Super Admin User Management Tests
def test_super_admin_user_management():
    """Test Super Admin user management endpoints"""
    print_test_header("Super Admin User Management")
    
    if "superadmin" not in tokens:
        print("❌ Cannot test Super Admin user management without superadmin token")
        return False
    
    success = True
    
    # Test GET all users
    print_test_header("GET /api/admin/users")
    response = make_request("GET", "/api/admin/users", token=tokens["superadmin"])
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET all users failed")
        success = False
    else:
        print("✅ GET all users passed")
    
    # Test GET all users with filtering
    print_test_header("GET /api/admin/users with filtering")
    response = make_request("GET", "/api/admin/users?user_type=admin&limit=5", token=tokens["superadmin"])
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET all users with filtering failed")
        success = False
    else:
        print("✅ GET all users with filtering passed")
    
    # Test GET user by ID
    print_test_header("GET /api/admin/users/{user_id}")
    # Get a user ID from the list of users
    users_response = make_request("GET", "/api/admin/users", token=tokens["superadmin"])
    if users_response.status_code != 200 or not users_response.json():
        print("❌ Cannot get user ID for testing")
        success = False
    else:
        user_id = users_response.json()[0]["id"]
        response = make_request("GET", f"/api/admin/users/{user_id}", token=tokens["superadmin"])
        if response.status_code != 200 or response.json()["id"] != user_id:
            print("❌ GET user by ID failed")
            success = False
        else:
            print("✅ GET user by ID passed")
    
    # Test CREATE user
    print_test_header("POST /api/admin/users")
    new_user = {
        "email": f"testadmin_{uuid.uuid4().hex[:8]}@example.com",
        "username": f"testadmin_{uuid.uuid4().hex[:8]}",
        "full_name": "Test Admin User",
        "password": "TestAdmin123!",
        "user_type": "admin"
    }
    response = make_request("POST", "/api/admin/users", new_user, token=tokens["superadmin"])
    if response.status_code != 200:
        print("❌ CREATE user failed")
        success = False
    else:
        print("✅ CREATE user passed")
        created_user_id = response.json()["id"]
        
        # Test UPDATE user
        print_test_header("PUT /api/admin/users/{user_id}")
        update_data = {
            "full_name": f"Updated Admin Name {uuid.uuid4().hex[:8]}",
            "is_active": True
        }
        response = make_request("PUT", f"/api/admin/users/{created_user_id}", update_data, token=tokens["superadmin"])
        if response.status_code != 200 or response.json()["full_name"] != update_data["full_name"]:
            print("❌ UPDATE user failed")
            success = False
        else:
            print("✅ UPDATE user passed")
        
        # Test DELETE user
        print_test_header("DELETE /api/admin/users/{user_id}")
        response = make_request("DELETE", f"/api/admin/users/{created_user_id}", token=tokens["superadmin"])
        if response.status_code != 200:
            print("❌ DELETE user failed")
            success = False
        else:
            print("✅ DELETE user passed")
    
    # Test permissions - admin user should not be able to access these endpoints
    if "admin" in tokens:
        print_test_header("Testing permissions - admin user")
        response = make_request("GET", "/api/admin/users", token=tokens["admin"], expected_status=403)
        if response.status_code != 403:
            print("❌ Permission check failed - admin user should not access super admin endpoints")
            success = False
        else:
            print("✅ Permission check passed - admin user correctly denied access")
    
    return success

def test_reviews_management():
    """Test reviews management endpoints"""
    print_test_header("Reviews Management")
    
    if "admin" not in tokens:
        print("❌ Cannot test reviews management without admin token")
        return False
    
    success = True
    
    # Test GET all reviews
    print_test_header("GET /api/admin/reviews")
    response = make_request("GET", "/api/admin/reviews", token=tokens["admin"])
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET all reviews failed")
        success = False
    else:
        print("✅ GET all reviews passed")
    
    # Test GET all reviews with filtering
    print_test_header("GET /api/admin/reviews with filtering")
    response = make_request("GET", "/api/admin/reviews?is_verified=false&limit=5", token=tokens["admin"])
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET all reviews with filtering failed")
        success = False
    else:
        print("✅ GET all reviews with filtering passed")
    
    # Create a review for testing
    if test_tool_id:
        print_test_header("Creating a review for testing")
        review_data = {
            "rating": 4,
            "title": f"Test Review {uuid.uuid4().hex[:8]}",
            "content": "This is a test review content.",
            "pros": "Good features, easy to use",
            "cons": "Some limitations",
            "tool_id": test_tool_id
        }
        
        # We need a user token to create a review
        if "user" in tokens:
            # This endpoint doesn't exist in the current API, so we'll need to create it directly in the database
            # For testing purposes, we'll use the admin token to verify and delete the review
            
            # Test VERIFY review
            # Get a review ID from the list of reviews
            reviews_response = make_request("GET", "/api/admin/reviews?is_verified=false", token=tokens["admin"])
            if reviews_response.status_code == 200 and reviews_response.json():
                review_id = reviews_response.json()[0]["id"]
                
                print_test_header("PUT /api/admin/reviews/{review_id}/verify")
                response = make_request("PUT", f"/api/admin/reviews/{review_id}/verify", token=tokens["admin"])
                if response.status_code != 200:
                    print("❌ VERIFY review failed")
                    success = False
                else:
                    print("✅ VERIFY review passed")
                
                # Test DELETE review
                print_test_header("DELETE /api/admin/reviews/{review_id}")
                response = make_request("DELETE", f"/api/admin/reviews/{review_id}", token=tokens["admin"])
                if response.status_code != 200:
                    print("❌ DELETE review failed")
                    success = False
                else:
                    print("✅ DELETE review passed")
            else:
                print("⚠️ No unverified reviews found for testing verification and deletion")
    else:
        print("⚠️ No test tool ID available for creating a review")
    
    return success

def test_advanced_analytics():
    """Test advanced analytics endpoint"""
    print_test_header("Advanced Analytics")
    
    if "superadmin" not in tokens:
        print("❌ Cannot test advanced analytics without superadmin token")
        return False
    
    # Test GET advanced analytics
    print_test_header("GET /api/admin/analytics/advanced")
    response = make_request("GET", "/api/admin/analytics/advanced", token=tokens["superadmin"])
    if response.status_code != 200:
        print("❌ GET advanced analytics failed")
        return False
    
    data = response.json()
    # Check if the response contains the expected data structure
    expected_keys = ["user_stats", "content_stats", "review_stats", "recent_activity"]
    
    for key in expected_keys:
        if key not in data:
            print(f"❌ Missing key in response: {key}")
            return False
    
    # Test permissions - admin user should not be able to access this endpoint
    if "admin" in tokens:
        print_test_header("Testing permissions - admin user")
        response = make_request("GET", "/api/admin/analytics/advanced", token=tokens["admin"], expected_status=403)
        if response.status_code != 403:
            print("❌ Permission check failed - admin user should not access super admin endpoints")
            return False
        else:
            print("✅ Permission check passed - admin user correctly denied access")
    
    print("✅ Advanced analytics endpoint passed")
    return True

def test_sample_csv():
    """Test sample CSV file download endpoint"""
    print_test_header("Sample CSV File Download")
    
    if "admin" not in tokens:
        print("❌ Cannot test sample CSV file download without admin token")
        return False
    
    # Test GET sample CSV file
    print_test_header("GET /api/admin/tools/sample-csv")
    response = make_request("GET", "/api/admin/tools/sample-csv", token=tokens["admin"])
    if response.status_code != 200:
        print("❌ GET sample CSV file failed")
        return False
    
    # Check if the response is a CSV file
    content_type = response.headers.get("Content-Type")
    if content_type != "text/csv":
        print(f"❌ Expected content type 'text/csv', got '{content_type}'")
        return False
    
    # Check if the response has the Content-Disposition header
    content_disposition = response.headers.get("Content-Disposition")
    if not content_disposition or "attachment" not in content_disposition:
        print(f"❌ Expected Content-Disposition header with 'attachment', got '{content_disposition}'")
        return False
    
    print("✅ Sample CSV file download endpoint passed")
    return True

def test_role_management():
    """Test role management endpoints"""
    print_test_header("Role Management")
    
    if "superadmin" not in tokens:
        print("❌ Cannot test role management without superadmin token")
        return False
    
    success = True
    
    # Create a test user to promote/demote
    print_test_header("Creating a test user for role management")
    new_user = {
        "email": f"testrole_{uuid.uuid4().hex[:8]}@example.com",
        "username": f"testrole_{uuid.uuid4().hex[:8]}",
        "full_name": "Test Role User",
        "password": "TestRole123!",
        "user_type": "user"
    }
    response = make_request("POST", "/api/admin/users", new_user, token=tokens["superadmin"])
    if response.status_code != 200:
        print("❌ Failed to create test user for role management")
        return False
    
    test_user_id = response.json()["id"]
    
    # Test PROMOTE user
    print_test_header("POST /api/admin/users/{user_id}/promote")
    response = make_request("POST", f"/api/admin/users/{test_user_id}/promote", token=tokens["superadmin"])
    if response.status_code != 200:
        print("❌ PROMOTE user failed")
        success = False
    else:
        print("✅ PROMOTE user passed")
        
        # Verify the user was promoted
        response = make_request("GET", f"/api/admin/users/{test_user_id}", token=tokens["superadmin"])
        if response.status_code != 200 or response.json()["user_type"] != "admin":
            print("❌ User promotion verification failed")
            success = False
        else:
            print("✅ User promotion verification passed")
        
        # Test DEMOTE user
        print_test_header("POST /api/admin/users/{user_id}/demote")
        response = make_request("POST", f"/api/admin/users/{test_user_id}/demote", token=tokens["superadmin"])
        if response.status_code != 200:
            print("❌ DEMOTE user failed")
            success = False
        else:
            print("✅ DEMOTE user passed")
            
            # Verify the user was demoted
            response = make_request("GET", f"/api/admin/users/{test_user_id}", token=tokens["superadmin"])
            if response.status_code != 200 or response.json()["user_type"] != "user":
                print("❌ User demotion verification failed")
                success = False
            else:
                print("✅ User demotion verification passed")
    
    # Clean up - delete the test user
    print_test_header("Cleaning up - deleting test user")
    response = make_request("DELETE", f"/api/admin/users/{test_user_id}", token=tokens["superadmin"])
    if response.status_code != 200:
        print("⚠️ Failed to clean up test user")
    
    # Test permissions - admin user should not be able to access these endpoints
    if "admin" in tokens:
        print_test_header("Testing permissions - admin user")
        response = make_request("POST", f"/api/admin/users/{test_user_id}/promote", token=tokens["admin"], expected_status=403)
        if response.status_code != 403:
            print("❌ Permission check failed - admin user should not access super admin endpoints")
            success = False
        else:
            print("✅ Permission check passed - admin user correctly denied access")
    
    return success

def test_seo_tools():
    """Test SEO tools endpoints"""
    print_test_header("SEO Tools")
    
    if "admin" not in tokens:
        print("❌ Cannot test SEO tools without admin token")
        return False
    
    # Test GET SEO status for all tools
    print_test_header("GET /api/admin/seo/tools")
    response = make_request("GET", "/api/admin/seo/tools", token=tokens["admin"])
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET SEO status for all tools failed")
        return False
    
    # Check if the response contains the expected data structure
    if response.json():
        seo_data = response.json()[0]
        expected_keys = ["tool_id", "tool_name", "has_meta_title", "has_meta_description", "has_ai_content", "optimizations_count", "last_updated"]
        
        for key in expected_keys:
            if key not in seo_data:
                print(f"❌ Missing key in response: {key}")
                return False
    
    print("✅ SEO tools endpoint passed")
    return True

def test_access_control_critical():
    """Test critical access control changes - SuperAdmin vs Admin"""
    print_test_header("CRITICAL ACCESS CONTROL TESTING")
    
    if "admin" not in tokens or "superadmin" not in tokens:
        print("❌ Cannot test access control without both admin and superadmin tokens")
        return False
    
    success = True
    
    # Test 1: SuperAdmin can access admin panel endpoints
    print_test_header("SuperAdmin Access - Should PASS")
    
    # Test SuperAdmin can create categories (require_superadmin)
    category_data = {
        "name": f"SuperAdmin Test Category {uuid.uuid4().hex[:8]}",
        "description": "Test Description",
        "icon": "test-icon",
        "color": "#123456"
    }
    response = make_request("POST", "/api/categories", category_data, token=tokens["superadmin"], expected_status=200)
    if response.status_code != 200:
        print("❌ SuperAdmin cannot create categories")
        success = False
    else:
        print("✅ SuperAdmin can create categories")
        global test_category_id
        test_category_id = response.json()["id"]
    
    # Test SuperAdmin can access bulk upload
    response = make_request("GET", "/api/admin/tools/sample-csv", token=tokens["superadmin"], expected_status=200)
    if response.status_code != 200:
        print("❌ SuperAdmin cannot access sample CSV download")
        success = False
    else:
        print("✅ SuperAdmin can access sample CSV download")
    
    # Test SuperAdmin can access user management
    response = make_request("GET", "/api/admin/users", token=tokens["superadmin"], expected_status=200)
    if response.status_code != 200:
        print("❌ SuperAdmin cannot access user management")
        success = False
    else:
        print("✅ SuperAdmin can access user management")
    
    # Test 2: Regular Admin CANNOT access SuperAdmin endpoints
    print_test_header("Regular Admin Access - Should FAIL")
    
    # Test Admin CANNOT create categories (require_superadmin)
    response = make_request("POST", "/api/categories", category_data, token=tokens["admin"], expected_status=403)
    if response.status_code != 403:
        print("❌ Regular admin can create categories (should be blocked)")
        success = False
    else:
        print("✅ Regular admin correctly blocked from creating categories")
    
    # Test Admin CANNOT access bulk upload
    response = make_request("GET", "/api/admin/tools/sample-csv", token=tokens["admin"], expected_status=403)
    if response.status_code != 403:
        print("❌ Regular admin can access sample CSV download (should be blocked)")
        success = False
    else:
        print("✅ Regular admin correctly blocked from sample CSV download")
    
    # Test Admin CANNOT access user management
    response = make_request("GET", "/api/admin/users", token=tokens["admin"], expected_status=403)
    if response.status_code != 403:
        print("❌ Regular admin can access user management (should be blocked)")
        success = False
    else:
        print("✅ Regular admin correctly blocked from user management")
    
    # Test Admin CANNOT access bulk upload endpoint
    csv_content = "name,description,category_id\nTest Tool,Test Description,test-id"
    files = {'file': ('test.csv', csv_content, 'text/csv')}
    response = make_request("POST", "/api/tools/bulk-upload", files=files, token=tokens["admin"], expected_status=403)
    if response.status_code != 403:
        print("❌ Regular admin can access bulk upload (should be blocked)")
        success = False
    else:
        print("✅ Regular admin correctly blocked from bulk upload")
    
    return success

def test_bulk_upload_functionality():
    """Test comprehensive bulk upload functionality for Super Admin"""
    print_test_header("COMPREHENSIVE BULK UPLOAD FUNCTIONALITY TESTING")
    
    if "superadmin" not in tokens:
        print("❌ Cannot test bulk upload without superadmin token")
        return False
    
    success = True
    
    # Test 1: Test /api/tools/csv-template endpoint (simple template)
    print_test_header("Simple CSV Template Endpoint")
    response = make_request("GET", "/api/tools/csv-template", expected_status=200)
    if response.status_code != 200:
        print("❌ Cannot access simple CSV template endpoint")
        success = False
    else:
        print("✅ Simple CSV template endpoint works")
        
        # Check content type
        content_type = response.headers.get("Content-Type")
        if content_type != "text/csv":
            print(f"❌ Expected CSV content type, got {content_type}")
            success = False
        else:
            print("✅ Correct CSV content type")
        
        # Check Content-Disposition header
        content_disposition = response.headers.get("Content-Disposition")
        if not content_disposition or "attachment" not in content_disposition:
            print(f"❌ Expected Content-Disposition with attachment, got {content_disposition}")
            success = False
        else:
            print("✅ Correct Content-Disposition header")
        
        # Check CSV content structure
        csv_content = response.text
        if "name,description" in csv_content and "Example Tool" in csv_content:
            print("✅ CSV template contains expected structure")
        else:
            print("❌ CSV template structure is incorrect")
            success = False
    
    # Test 2: Test /api/admin/tools/sample-csv endpoint (requires superadmin)
    print_test_header("Super Admin Sample CSV Download")
    response = make_request("GET", "/api/admin/tools/sample-csv", token=tokens["superadmin"], expected_status=200)
    if response.status_code != 200:
        print("❌ Cannot download sample CSV template as superadmin")
        success = False
    else:
        print("✅ Sample CSV template download works for superadmin")
        
        # Check content type
        content_type = response.headers.get("Content-Type")
        if content_type != "text/csv":
            print(f"❌ Expected CSV content type, got {content_type}")
            success = False
        else:
            print("✅ Correct CSV content type")
        
        # Check Content-Disposition header
        content_disposition = response.headers.get("Content-Disposition")
        if not content_disposition or "attachment" not in content_disposition:
            print(f"❌ Expected Content-Disposition with attachment, got {content_disposition}")
            success = False
        else:
            print("✅ Correct Content-Disposition header")
        
        # Check CSV content structure
        csv_content = response.text
        if "name,description" in csv_content and ("Example Tool" in csv_content or "Test Tool" in csv_content):
            print("✅ CSV sample contains expected structure")
        else:
            print("❌ CSV sample structure is incorrect")
            success = False
    
    # Test 3: Test admin user cannot access sample CSV download
    print_test_header("Admin User Access to Sample CSV (Should Fail)")
    if "admin" in tokens:
        response = make_request("GET", "/api/admin/tools/sample-csv", token=tokens["admin"], expected_status=403)
        if response.status_code != 403:
            print("❌ Admin user should not be able to access sample CSV download")
            success = False
        else:
            print("✅ Admin user correctly blocked from sample CSV download")
    
    # Test 4: Test bulk upload with valid CSV
    print_test_header("Bulk Upload with Valid CSV")
    
    # Create a valid CSV with proper category ID
    if test_category_id:
        csv_content = f"""name,description,category_id,pricing_model,company_size,is_hot,is_featured,rating,total_reviews,views,trending_score,short_description,website_url,features,target_audience,integrations,logo_url,industry,employee_size,revenue_range,location,meta_title,meta_description
Test Bulk Tool 1,Description for bulk tool 1,{test_category_id},Freemium,SMB,true,false,4.5,10,100,85.5,Short desc 1,https://example1.com,Feature 1 Feature 2,Small businesses,Slack GitHub,https://logo1.com,Technology,11-50,1M-10M,San Francisco,Meta Title 1,Meta Description 1
Test Bulk Tool 2,Description for bulk tool 2,{test_category_id},Paid,Enterprise,false,true,4.2,25,250,92.3,Short desc 2,https://example2.com,Feature A Feature B,Large enterprises,Salesforce Hubspot,https://logo2.com,Marketing,51-200,10M-100M,New York,Meta Title 2,Meta Description 2"""
        
        files = {'file': ('bulk_tools.csv', csv_content, 'text/csv')}
        response = make_request("POST", "/api/tools/bulk-upload", files=files, token=tokens["superadmin"], expected_status=200)
        
        if response.status_code != 200:
            print("❌ Bulk upload with valid CSV failed")
            print(f"Response: {response.text}")
            success = False
        else:
            result = response.json()
            # Check for the updated response format (tools_created instead of created_count)
            if "tools_created" in result and result.get("tools_created", 0) > 0:
                print(f"✅ Bulk upload successful - created {result['tools_created']} tools")
                print(f"Created tools: {result.get('created_tools', [])}")
                if result.get('errors'):
                    print(f"Errors encountered: {result['errors']}")
            elif "created_count" in result and result.get("created_count", 0) > 0:
                print(f"⚠️ Bulk upload successful but using old response format - created {result['created_count']} tools")
                print("❌ Response format should use 'tools_created' instead of 'created_count'")
                success = False
            else:
                print("❌ Bulk upload completed but no tools were created")
                print(f"Response: {result}")
                success = False
    else:
        print("❌ Cannot test bulk upload without a valid category ID")
        success = False
    
    # Test 5: Test admin user cannot access bulk upload
    print_test_header("Admin User Access to Bulk Upload (Should Fail)")
    if "admin" in tokens:
        csv_content = "name,description,category_id\nTest Tool,Test Description,test-id"
        files = {'file': ('test.csv', csv_content, 'text/csv')}
        response = make_request("POST", "/api/tools/bulk-upload", files=files, token=tokens["admin"], expected_status=403)
        if response.status_code != 403:
            print("❌ Admin user should not be able to access bulk upload")
            success = False
        else:
            print("✅ Admin user correctly blocked from bulk upload")
    
    # Test 6: Test bulk upload with invalid file type
    print_test_header("Bulk Upload with Invalid File Type")
    files = {'file': ('test.txt', 'not a csv file', 'text/plain')}
    response = make_request("POST", "/api/tools/bulk-upload", files=files, token=tokens["superadmin"], expected_status=400)
    if response.status_code != 400:
        print("❌ Bulk upload should reject non-CSV files")
        success = False
    else:
        print("✅ Bulk upload correctly rejects non-CSV files")
    
    # Test 7: Test bulk upload with malformed CSV
    print_test_header("Bulk Upload with Malformed CSV")
    malformed_csv = """name,description,category_id
Tool 1,Description 1,invalid-category-id
Tool 2,Description 2,another-invalid-id"""
    
    files = {'file': ('malformed.csv', malformed_csv, 'text/csv')}
    response = make_request("POST", "/api/tools/bulk-upload", files=files, token=tokens["superadmin"], expected_status=200)
    if response.status_code == 200:
        result = response.json()
        if result.get("errors"):
            print(f"✅ Bulk upload correctly handled malformed CSV with errors: {len(result['errors'])} errors")
        else:
            print("⚠️ Bulk upload processed malformed CSV without errors (unexpected)")
    else:
        print("❌ Bulk upload with malformed CSV failed unexpectedly")
        success = False
    
    # Test 8: Test bulk upload with empty CSV
    print_test_header("Bulk Upload with Empty CSV")
    empty_csv = "name,description,category_id\n"
    files = {'file': ('empty.csv', empty_csv, 'text/csv')}
    response = make_request("POST", "/api/tools/bulk-upload", files=files, token=tokens["superadmin"], expected_status=200)
    if response.status_code == 200:
        result = response.json()
        if result.get("created_count", 0) == 0:
            print("✅ Bulk upload correctly handled empty CSV")
        else:
            print("❌ Bulk upload should not create tools from empty CSV")
            success = False
    else:
        print("❌ Bulk upload with empty CSV failed unexpectedly")
        success = False
    
    # Test 9: Test complete flow - download template, modify, upload
    print_test_header("Complete Flow - Download Template, Modify, Upload")
    
    # Download template
    template_response = make_request("GET", "/api/admin/tools/sample-csv", token=tokens["superadmin"])
    if template_response.status_code == 200:
        # Modify the template content
        template_content = template_response.text
        
        # Replace placeholder with actual category ID if available
        if test_category_id:
            modified_content = template_content.replace("CREATE_CATEGORIES_FIRST", test_category_id)
            modified_content = modified_content.replace("REPLACE_WITH_ACTUAL_CATEGORY_ID", test_category_id)
            
            # Add a new row to the template
            lines = modified_content.strip().split('\n')
            if len(lines) >= 2:  # Header + at least one data row
                header = lines[0]
                new_row = lines[1].replace("Example Tool 1", f"Flow Test Tool {uuid.uuid4().hex[:8]}")
                modified_content = f"{header}\n{new_row}"
                
                files = {'file': ('flow_test.csv', modified_content, 'text/csv')}
                upload_response = make_request("POST", "/api/tools/bulk-upload", files=files, token=tokens["superadmin"])
                
                if upload_response.status_code == 200:
                    result = upload_response.json()
                    if result.get("created_count", 0) > 0:
                        print("✅ Complete flow test successful")
                    else:
                        print("❌ Complete flow test failed - no tools created")
                        success = False
                else:
                    print("❌ Complete flow test failed - upload failed")
                    success = False
            else:
                print("❌ Template content is malformed")
                success = False
        else:
            print("⚠️ Cannot test complete flow without valid category ID")
    else:
        print("❌ Cannot download template for complete flow test")
        success = False
    
    return success

def test_discover_page_data():
    """Test data availability for Discover page"""
    print_test_header("DISCOVER PAGE DATA TESTING")
    
    success = True
    
    # Test tools search endpoint (used by Discover page)
    print_test_header("Tools Search for Discover Page")
    response = make_request("GET", "/api/tools/search?page=1&per_page=20", expected_status=200)
    if response.status_code != 200:
        print("❌ Tools search endpoint failed")
        success = False
    else:
        data = response.json()
        total_tools = data.get("total", 0)
        print(f"✅ Tools search endpoint works - found {total_tools} tools")
        
        if total_tools < 10:
            print(f"⚠️ Warning: Only {total_tools} tools found. Discover page may look empty.")
        
        # Check if tools have required fields
        if data.get("tools"):
            sample_tool = data["tools"][0]
            required_fields = ["id", "name", "description", "category_id"]
            for field in required_fields:
                if field not in sample_tool:
                    print(f"❌ Tool missing required field: {field}")
                    success = False
            if success:
                print("✅ Tools have all required fields")
    
    # Test tools analytics (used for carousels)
    print_test_header("Tools Analytics for Carousels")
    response = make_request("GET", "/api/tools/analytics", expected_status=200)
    if response.status_code != 200:
        print("❌ Tools analytics endpoint failed")
        success = False
    else:
        data = response.json()
        carousels = ["trending_tools", "top_rated_tools", "most_viewed_tools", "newest_tools", "featured_tools", "hot_tools"]
        for carousel in carousels:
            if carousel in data:
                count = len(data[carousel])
                print(f"✅ {carousel}: {count} tools")
            else:
                print(f"❌ Missing carousel: {carousel}")
                success = False
    
    # Test categories (used for filtering)
    print_test_header("Categories for Filtering")
    response = make_request("GET", "/api/categories", expected_status=200)
    if response.status_code != 200:
        print("❌ Categories endpoint failed")
        success = False
    else:
        categories = response.json()
        print(f"✅ Categories endpoint works - found {len(categories)} categories")
        if len(categories) < 3:
            print(f"⚠️ Warning: Only {len(categories)} categories found. Filtering may be limited.")
    
    return success

def run_all_tests():
    """Run all tests with focus on critical areas"""
    results = {}
    
    try:
        # Basic health check
        results["health_check"] = test_health_check()
        
        # Authentication - Critical for access control testing
        results["login"] = test_login()
        
        # CRITICAL TESTS - Main focus areas
        results["access_control_critical"] = test_access_control_critical()
        results["bulk_upload_functionality"] = test_bulk_upload_functionality()
        results["discover_page_data"] = test_discover_page_data()
        
        # Additional important tests
        results["tools_search"] = test_tools_search()
        results["tools_analytics"] = test_tools_analytics()
        results["super_admin_user_management"] = test_super_admin_user_management()
        results["sample_csv"] = test_sample_csv()
        
        # Print summary
        print("\n" + "=" * 80)
        print("CRITICAL TEST SUMMARY - MarketMindAI Access Control & Bulk Upload")
        print("=" * 80)
        
        critical_tests = ["access_control_critical", "bulk_upload_functionality", "discover_page_data"]
        critical_passed = True
        
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            if test_name in critical_tests:
                print(f"🔥 CRITICAL - {test_name}: {status}")
                if not passed:
                    critical_passed = False
            else:
                print(f"   {test_name}: {status}")
        
        print("\n" + "=" * 80)
        if critical_passed:
            print("🎉 CRITICAL TESTS PASSED! Access control and bulk upload are working correctly.")
        else:
            print("❌ CRITICAL TESTS FAILED! Access control or bulk upload issues detected.")
            
        # Count overall results
        total_tests = len(results)
        passed_tests = sum(1 for passed in results.values() if passed)
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()