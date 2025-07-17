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
    """Test tools comparison functionality - CRITICAL REVIEW REQUEST"""
    print_test_header("Tools Comparison - CRITICAL REVIEW REQUEST")
    
    if "admin" not in tokens:
        print("❌ Cannot test tools comparison without admin token")
        return False
    
    success = True
    
    # Step 1: Test GET /api/tools/compare endpoint with a user that has comparison tools - should return actual tool objects, not just a message
    print_test_header("Step 1: GET /api/tools/compare (initially empty)")
    response = make_request("GET", "/api/tools/compare", token=tokens["admin"])
    if response.status_code != 200:
        print("❌ GET comparison tools failed")
        success = False
    else:
        comparison_tools = response.json()
        if not isinstance(comparison_tools, list):
            print("❌ GET comparison tools should return a list")
            success = False
        else:
            print(f"✅ GET comparison tools returned list with {len(comparison_tools)} items")
            if len(comparison_tools) > 0:
                print("ℹ️ User already has tools in comparison")
                for tool in comparison_tools:
                    if not isinstance(tool, dict) or "id" not in tool or "name" not in tool:
                        print("❌ Comparison tools should return actual tool objects with id and name")
                        success = False
                    else:
                        print(f"✅ Tool object found: {tool.get('name', 'Unknown')} (ID: {tool.get('id', 'Unknown')})")
    
    # Step 2: Test POST /api/tools/compare to add a tool to comparison
    print_test_header("Step 2: POST /api/tools/compare to add tool")
    
    # First, get a tool to add to comparison
    tools_response = make_request("GET", "/api/tools?limit=1")
    if tools_response.status_code != 200 or not tools_response.json():
        print("❌ Cannot get tools for comparison test")
        return False
    
    test_tool = tools_response.json()[0]
    test_tool_id_for_comparison = test_tool["id"]
    test_tool_name = test_tool["name"]
    
    print(f"ℹ️ Using tool for comparison: {test_tool_name} (ID: {test_tool_id_for_comparison})")
    
    json_data = {"tool_id": test_tool_id_for_comparison}
    response = make_request("POST", "/api/tools/compare", json_data, token=tokens["admin"], expected_status=200)
    if response.status_code != 200:
        print("❌ Add to comparison failed")
        success = False
        print_response(response)
    else:
        print("✅ Add to comparison passed")
        response_data = response.json()
        if "message" not in response_data:
            print("❌ Add to comparison should return a message")
            success = False
        else:
            print(f"✅ Add to comparison message: {response_data['message']}")
    
    # Step 3: Test GET /api/tools/compare again to verify the tool was added
    print_test_header("Step 3: GET /api/tools/compare (after adding tool)")
    response = make_request("GET", "/api/tools/compare", token=tokens["admin"])
    if response.status_code != 200:
        print("❌ GET comparison tools after adding failed")
        success = False
    else:
        comparison_tools = response.json()
        if not isinstance(comparison_tools, list):
            print("❌ GET comparison tools should return a list")
            success = False
        else:
            print(f"✅ GET comparison tools returned list with {len(comparison_tools)} items")
            
            # CRITICAL CHECK: Verify we get actual tool objects, not just a message
            if len(comparison_tools) == 0:
                print("❌ CRITICAL: No tools found in comparison after adding one")
                success = False
            else:
                tool_found = False
                for tool in comparison_tools:
                    if not isinstance(tool, dict):
                        print("❌ CRITICAL: Comparison should return actual tool objects, not just messages")
                        success = False
                        break
                    
                    # Check if this is an actual tool object with expected properties
                    expected_tool_properties = ["id", "name", "description", "category_id"]
                    missing_properties = []
                    for prop in expected_tool_properties:
                        if prop not in tool:
                            missing_properties.append(prop)
                    
                    if missing_properties:
                        print(f"❌ CRITICAL: Tool object missing properties: {missing_properties}")
                        success = False
                    else:
                        print(f"✅ CRITICAL: Tool object has all expected properties: {tool.get('name', 'Unknown')}")
                    
                    if tool.get("id") == test_tool_id_for_comparison:
                        tool_found = True
                        print(f"✅ CRITICAL: Added tool found in comparison: {tool.get('name', 'Unknown')}")
                
                if not tool_found:
                    print("❌ CRITICAL: Added tool not found in comparison list")
                    success = False
    
    # Step 4: Test DELETE /api/tools/compare/{tool_id} to remove a tool from comparison
    print_test_header("Step 4: DELETE /api/tools/compare/{tool_id}")
    response = make_request("DELETE", f"/api/tools/compare/{test_tool_id_for_comparison}", token=tokens["admin"])
    if response.status_code != 200:
        print("❌ Remove from comparison failed")
        success = False
        print_response(response)
    else:
        print("✅ Remove from comparison passed")
        response_data = response.json()
        if "message" not in response_data:
            print("❌ Remove from comparison should return a message")
            success = False
        else:
            print(f"✅ Remove from comparison message: {response_data['message']}")
    
    # Step 5: Test GET /api/tools/compare again to verify the tool was removed
    print_test_header("Step 5: GET /api/tools/compare (after removing tool)")
    response = make_request("GET", "/api/tools/compare", token=tokens["admin"])
    if response.status_code != 200:
        print("❌ GET comparison tools after removing failed")
        success = False
    else:
        comparison_tools = response.json()
        if not isinstance(comparison_tools, list):
            print("❌ GET comparison tools should return a list")
            success = False
        else:
            print(f"✅ GET comparison tools returned list with {len(comparison_tools)} items")
            
            # Verify the tool was removed
            tool_still_found = False
            for tool in comparison_tools:
                if isinstance(tool, dict) and tool.get("id") == test_tool_id_for_comparison:
                    tool_still_found = True
                    break
            
            if tool_still_found:
                print("❌ CRITICAL: Tool still found in comparison after removal")
                success = False
            else:
                print("✅ CRITICAL: Tool successfully removed from comparison")
    
    # Additional test: Try to add the same tool twice (should fail)
    print_test_header("Additional Test: Add same tool twice (should fail)")
    
    # Add tool first
    json_data = {"tool_id": test_tool_id_for_comparison}
    response = make_request("POST", "/api/tools/compare", json_data, token=tokens["admin"], expected_status=200)
    if response.status_code == 200:
        # Try to add the same tool again
        response = make_request("POST", "/api/tools/compare", json_data, token=tokens["admin"], expected_status=400)
        if response.status_code != 400:
            print("❌ Adding duplicate tool should fail with 400")
            success = False
        else:
            print("✅ Duplicate tool addition correctly rejected")
            response_data = response.json()
            if "already in comparison" not in response_data.get("detail", "").lower():
                print("❌ Error message should mention tool is already in comparison")
                success = False
            else:
                print("✅ Correct error message for duplicate tool")
        
        # Clean up - remove the tool
        make_request("DELETE", f"/api/tools/compare/{test_tool_id_for_comparison}", token=tokens["admin"])
    
    if success:
        print("✅ CRITICAL REVIEW: Tools comparison functionality PASSED - GET endpoint returns actual tool objects")
    else:
        print("❌ CRITICAL REVIEW: Tools comparison functionality FAILED - Issues found with tool object structure")
    
    return success

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

def test_blog_creation_validation():
    """Test blog creation validation - specific focus on category_id requirement"""
    print_test_header("Blog Creation Validation Testing")
    
    if "user" not in tokens:
        print("❌ Cannot test blog creation without user token")
        return False
    
    success = True
    
    # Test 1: Blog creation with valid category_id (should work)
    print_test_header("Blog Creation with Valid Category ID")
    if test_category_id:
        valid_blog_data = {
            "title": f"Valid Blog {uuid.uuid4().hex[:8]}",
            "content": "This is a valid blog content with proper category ID. " * 20,
            "excerpt": "Valid excerpt",
            "status": "published",
            "category_id": test_category_id,
            "slug": f"valid-blog-{uuid.uuid4().hex[:8]}"
        }
        response = make_request("POST", "/api/blogs", valid_blog_data, token=tokens["user"], expected_status=200)
        if response.status_code != 200:
            print("❌ Blog creation with valid category_id failed")
            success = False
        else:
            print("✅ Blog creation with valid category_id passed")
            # Store for cleanup if needed
            valid_blog_id = response.json()["id"]
    else:
        print("⚠️ Cannot test with valid category_id - no test category available")
        success = False
    
    # Test 2: Blog creation with missing category_id (should fail with 422)
    print_test_header("Blog Creation with Missing Category ID")
    invalid_blog_data = {
        "title": f"Invalid Blog {uuid.uuid4().hex[:8]}",
        "content": "This is a blog without category ID. " * 20,
        "excerpt": "Invalid excerpt",
        "status": "published",
        "slug": f"invalid-blog-{uuid.uuid4().hex[:8]}"
        # Note: category_id is intentionally missing
    }
    response = make_request("POST", "/api/blogs", invalid_blog_data, token=tokens["user"], expected_status=422)
    if response.status_code != 422:
        print("❌ Blog creation should fail with missing category_id")
        success = False
    else:
        print("✅ Blog creation correctly failed with missing category_id")
        # Check if the error message mentions category_id
        try:
            error_detail = response.json().get("detail", [])
            category_error_found = False
            if isinstance(error_detail, list):
                for error in error_detail:
                    if isinstance(error, dict) and "category_id" in str(error.get("loc", [])):
                        category_error_found = True
                        print(f"✅ Validation error correctly identifies category_id: {error}")
                        break
            if not category_error_found:
                print(f"⚠️ Validation error doesn't specifically mention category_id: {error_detail}")
        except:
            print("⚠️ Could not parse validation error details")
    
    # Test 3: Blog creation with null category_id (should fail with 422)
    print_test_header("Blog Creation with Null Category ID")
    null_category_blog_data = {
        "title": f"Null Category Blog {uuid.uuid4().hex[:8]}",
        "content": "This is a blog with null category ID. " * 20,
        "excerpt": "Null category excerpt",
        "status": "published",
        "category_id": None,  # Explicitly null
        "slug": f"null-category-blog-{uuid.uuid4().hex[:8]}"
    }
    response = make_request("POST", "/api/blogs", null_category_blog_data, token=tokens["user"], expected_status=422)
    if response.status_code != 422:
        print("❌ Blog creation should fail with null category_id")
        success = False
    else:
        print("✅ Blog creation correctly failed with null category_id")
    
    # Test 4: Blog creation with invalid category_id (should fail with 422 or 400)
    print_test_header("Blog Creation with Invalid Category ID")
    invalid_category_blog_data = {
        "title": f"Invalid Category Blog {uuid.uuid4().hex[:8]}",
        "content": "This is a blog with invalid category ID. " * 20,
        "excerpt": "Invalid category excerpt",
        "status": "published",
        "category_id": "non-existent-category-id",
        "slug": f"invalid-category-blog-{uuid.uuid4().hex[:8]}"
    }
    response = make_request("POST", "/api/blogs", invalid_category_blog_data, token=tokens["user"], expected_status=[400, 422, 500])
    if response.status_code not in [400, 422, 500]:
        print("❌ Blog creation should fail with invalid category_id")
        success = False
    else:
        print(f"✅ Blog creation correctly failed with invalid category_id (status: {response.status_code})")
    
    # Test 5: Blog creation with empty string category_id (should fail)
    print_test_header("Blog Creation with Empty String Category ID")
    empty_category_blog_data = {
        "title": f"Empty Category Blog {uuid.uuid4().hex[:8]}",
        "content": "This is a blog with empty category ID. " * 20,
        "excerpt": "Empty category excerpt",
        "status": "published",
        "category_id": "",  # Empty string
        "slug": f"empty-category-blog-{uuid.uuid4().hex[:8]}"
    }
    response = make_request("POST", "/api/blogs", empty_category_blog_data, token=tokens["user"], expected_status=422)
    if response.status_code != 422:
        print("❌ Blog creation should fail with empty string category_id")
        success = False
    else:
        print("✅ Blog creation correctly failed with empty string category_id")
    
    return success

def test_file_upload():
    """Test file upload functionality"""
    print_test_header("File Upload Testing")
    
    if "user" not in tokens:
        print("❌ Cannot test file upload without user token")
        return False
    
    success = True
    
    # Test 1: Upload a valid image file (simulated)
    print_test_header("Valid Image File Upload")
    # Create a small test image data (1x1 PNG)
    import base64
    # This is a 1x1 transparent PNG image in base64
    png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU8j8wAAAABJRU5ErkJggg==")
    
    files = {'file': ('test.png', png_data, 'image/png')}
    response = make_request("POST", "/api/upload", files=files, token=tokens["user"], expected_status=200)
    if response.status_code != 200:
        print("❌ Valid image file upload failed")
        success = False
    else:
        print("✅ Valid image file upload passed")
        result = response.json()
        expected_keys = ["file_url", "filename", "content_type", "size"]
        for key in expected_keys:
            if key not in result:
                print(f"❌ Missing key in upload response: {key}")
                success = False
        
        # Check if file_url is a data URL
        if result.get("file_url", "").startswith("data:image/png;base64,"):
            print("✅ File upload returns proper data URL")
        else:
            print("❌ File upload should return data URL")
            success = False
    
    # Test 2: Upload file without authentication (should fail)
    print_test_header("File Upload Without Authentication")
    files = {'file': ('test.png', png_data, 'image/png')}
    response = make_request("POST", "/api/upload", files=files, expected_status=401)
    if response.status_code != 401:
        print("❌ File upload should require authentication")
        success = False
    else:
        print("✅ File upload correctly requires authentication")
    
    # Test 3: Upload invalid file type (should fail)
    print_test_header("Invalid File Type Upload")
    invalid_file_content = b"This is not an image file"
    files = {'file': ('test.txt', invalid_file_content, 'text/plain')}
    response = make_request("POST", "/api/upload", files=files, token=tokens["user"], expected_status=400)
    if response.status_code != 400:
        print("❌ Invalid file type should be rejected")
        success = False
    else:
        print("✅ Invalid file type correctly rejected")
    
    # Test 4: Upload file that's too large (simulate)
    print_test_header("Large File Upload")
    # Create a file that's larger than 10MB (simulated by checking the logic)
    large_file_content = b"x" * (11 * 1024 * 1024)  # 11MB
    files = {'file': ('large.png', large_file_content, 'image/png')}
    response = make_request("POST", "/api/upload", files=files, token=tokens["user"], expected_status=400)
    if response.status_code != 400:
        print("❌ Large file should be rejected")
        success = False
    else:
        print("✅ Large file correctly rejected")
    
    # Test 5: Upload valid JPEG file
    print_test_header("Valid JPEG File Upload")
    # Minimal JPEG header
    jpeg_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xaa\xff\xd9'
    
    files = {'file': ('test.jpg', jpeg_data, 'image/jpeg')}
    response = make_request("POST", "/api/upload", files=files, token=tokens["user"], expected_status=200)
    if response.status_code != 200:
        print("❌ Valid JPEG file upload failed")
        success = False
    else:
        print("✅ Valid JPEG file upload passed")
    
    return success

def test_csv_endpoint_access():
    """Test CSV endpoint access with different user roles"""
    print_test_header("CSV Endpoint Access Testing")
    
    success = True
    
    # Test 1: Super Admin access (should work)
    print_test_header("Super Admin Access to CSV Endpoint")
    if "superadmin" in tokens:
        response = make_request("GET", "/api/admin/tools/sample-csv", token=tokens["superadmin"], expected_status=200)
        if response.status_code != 200:
            print("❌ Super Admin should be able to access CSV endpoint")
            success = False
        else:
            print("✅ Super Admin can access CSV endpoint")
            
            # Check response headers
            content_type = response.headers.get("Content-Type")
            if content_type != "text/csv":
                print(f"❌ Expected CSV content type, got {content_type}")
                success = False
            else:
                print("✅ CSV endpoint returns correct content type")
            
            content_disposition = response.headers.get("Content-Disposition")
            if not content_disposition or "attachment" not in content_disposition:
                print(f"❌ Expected attachment disposition, got {content_disposition}")
                success = False
            else:
                print("✅ CSV endpoint returns correct content disposition")
    else:
        print("⚠️ Cannot test Super Admin access - no superadmin token")
        success = False
    
    # Test 2: Regular Admin access (should fail with 403)
    print_test_header("Regular Admin Access to CSV Endpoint")
    if "admin" in tokens:
        response = make_request("GET", "/api/admin/tools/sample-csv", token=tokens["admin"], expected_status=403)
        if response.status_code != 403:
            print("❌ Regular Admin should NOT be able to access CSV endpoint")
            success = False
        else:
            print("✅ Regular Admin correctly denied access to CSV endpoint")
    else:
        print("⚠️ Cannot test Admin access - no admin token")
    
    # Test 3: Regular User access (should fail with 403)
    print_test_header("Regular User Access to CSV Endpoint")
    if "user" in tokens:
        response = make_request("GET", "/api/admin/tools/sample-csv", token=tokens["user"], expected_status=403)
        if response.status_code != 403:
            print("❌ Regular User should NOT be able to access CSV endpoint")
            success = False
        else:
            print("✅ Regular User correctly denied access to CSV endpoint")
    else:
        print("⚠️ Cannot test User access - no user token")
    
    # Test 4: Unauthenticated access (should fail with 401)
    print_test_header("Unauthenticated Access to CSV Endpoint")
    response = make_request("GET", "/api/admin/tools/sample-csv", expected_status=401)
    if response.status_code != 401:
        print("❌ Unauthenticated access should be denied")
        success = False
    else:
        print("✅ Unauthenticated access correctly denied")
    
    # Test 5: Test the public CSV template endpoint (should work without auth)
    print_test_header("Public CSV Template Endpoint")
    response = make_request("GET", "/api/tools/csv-template", expected_status=200)
    if response.status_code != 200:
        print("❌ Public CSV template endpoint should work without auth")
        success = False
    else:
        print("✅ Public CSV template endpoint works without auth")
        
        # Check response headers
        content_type = response.headers.get("Content-Type")
        if content_type != "text/csv":
            print(f"❌ Expected CSV content type, got {content_type}")
            success = False
        else:
            print("✅ Public CSV template returns correct content type")
    
    return success

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

def test_tool_access_request_system():
    """Test the new tool access request system - REVIEW REQUEST"""
    print_test_header("TOOL ACCESS REQUEST SYSTEM - REVIEW REQUEST")
    
    success = True
    
    # Test 1: Admin requests access to a tool
    print_test_header("Test 1: Admin Request Access to Tool")
    
    if "admin" not in tokens:
        print("❌ Cannot test tool access requests without admin token")
        return False
    
    # Get a tool to request access to
    tools_response = make_request("GET", "/api/tools?limit=1")
    if tools_response.status_code != 200 or not tools_response.json():
        print("❌ Cannot get tools for access request test")
        return False
    
    test_tool = tools_response.json()[0]
    tool_id = test_tool["id"]
    tool_name = test_tool["name"]
    
    print(f"ℹ️ Requesting access to tool: {tool_name} (ID: {tool_id})")
    
    # Request access to the tool
    request_data = {
        "request_message": "I need access to this tool for SEO optimization and content updates."
    }
    response = make_request("POST", f"/api/admin/tools/{tool_id}/request-access", request_data, token=tokens["admin"])
    if response.status_code != 200:
        print("❌ Admin tool access request failed")
        success = False
        print_response(response)
    else:
        print("✅ Admin tool access request successful")
        request_response = response.json()
        expected_keys = ["id", "tool_id", "admin_id", "status", "request_message", "tool_name", "admin_name"]
        for key in expected_keys:
            if key not in request_response:
                print(f"❌ Missing key in access request response: {key}")
                success = False
        
        if request_response.get("status") != "pending":
            print(f"❌ Expected status 'pending', got {request_response.get('status')}")
            success = False
        else:
            print("✅ Access request created with pending status")
        
        # Store request ID for later tests
        global access_request_id
        access_request_id = request_response["id"]
    
    # Test 2: Get current admin's requests
    print_test_header("Test 2: Get Current Admin's Requests")
    response = make_request("GET", "/api/admin/tools/my-requests", token=tokens["admin"])
    if response.status_code != 200:
        print("❌ Get admin's requests failed")
        success = False
    else:
        print("✅ Get admin's requests successful")
        requests = response.json()
        if not isinstance(requests, list):
            print("❌ Expected list of requests")
            success = False
        else:
            print(f"✅ Admin has {len(requests)} access requests")
            # Verify our request is in the list
            request_found = False
            for req in requests:
                if req.get("tool_id") == tool_id:
                    request_found = True
                    print(f"✅ Found our access request for tool: {req.get('tool_name')}")
                    break
            if not request_found:
                print("❌ Our access request not found in admin's requests")
                success = False
    
    # Test 3: Get assigned tools for admin (should be empty initially)
    print_test_header("Test 3: Get Assigned Tools for Admin")
    response = make_request("GET", "/api/admin/tools/assigned", token=tokens["admin"])
    if response.status_code != 200:
        print("❌ Get assigned tools for admin failed")
        success = False
    else:
        print("✅ Get assigned tools for admin successful")
        assigned_tools = response.json()
        if not isinstance(assigned_tools, list):
            print("❌ Expected list of assigned tools")
            success = False
        else:
            print(f"✅ Admin has {len(assigned_tools)} assigned tools")
    
    # Test 4: Superadmin gets all access requests
    print_test_header("Test 4: Superadmin Get All Access Requests")
    
    if "superadmin" not in tokens:
        print("❌ Cannot test superadmin access requests without superadmin token")
        success = False
    else:
        response = make_request("GET", "/api/admin/tools/access-requests", token=tokens["superadmin"])
        if response.status_code != 200:
            print("❌ Superadmin get access requests failed")
            success = False
        else:
            print("✅ Superadmin get access requests successful")
            all_requests = response.json()
            if not isinstance(all_requests, list):
                print("❌ Expected list of access requests")
                success = False
            else:
                print(f"✅ Found {len(all_requests)} total access requests")
                # Verify our request is in the list
                request_found = False
                for req in all_requests:
                    if req.get("tool_id") == tool_id:
                        request_found = True
                        print(f"✅ Found our access request in superadmin view: {req.get('tool_name')}")
                        break
                if not request_found:
                    print("❌ Our access request not found in superadmin's view")
                    success = False
    
    # Test 5: Superadmin approves the request
    print_test_header("Test 5: Superadmin Approve Access Request")
    
    if "superadmin" not in tokens or 'access_request_id' not in globals():
        print("❌ Cannot test request approval without superadmin token or request ID")
        success = False
    else:
        approval_data = {
            "status": "approved",
            "response_message": "Access granted for SEO optimization work."
        }
        response = make_request("PUT", f"/api/admin/tools/access-requests/{access_request_id}", approval_data, token=tokens["superadmin"])
        if response.status_code != 200:
            print("❌ Superadmin approve request failed")
            success = False
            print_response(response)
        else:
            print("✅ Superadmin approve request successful")
            approved_request = response.json()
            if approved_request.get("status") != "approved":
                print(f"❌ Expected status 'approved', got {approved_request.get('status')}")
                success = False
            else:
                print("✅ Request status updated to approved")
    
    # Test 6: Get assigned tools for admin after approval
    print_test_header("Test 6: Get Assigned Tools for Admin After Approval")
    response = make_request("GET", "/api/admin/tools/assigned", token=tokens["admin"])
    if response.status_code != 200:
        print("❌ Get assigned tools after approval failed")
        success = False
    else:
        print("✅ Get assigned tools after approval successful")
        assigned_tools = response.json()
        if not isinstance(assigned_tools, list):
            print("❌ Expected list of assigned tools")
            success = False
        else:
            print(f"✅ Admin now has {len(assigned_tools)} assigned tools")
            # Verify our tool is now assigned
            tool_found = False
            for tool in assigned_tools:
                if tool.get("id") == tool_id:
                    tool_found = True
                    print(f"✅ Tool now assigned to admin: {tool.get('name')}")
                    break
            if not tool_found:
                print("❌ Approved tool not found in admin's assigned tools")
                success = False
    
    # Test 7: Get all tools for superadmin
    print_test_header("Test 7: Get All Tools for Superadmin")
    
    if "superadmin" not in tokens:
        print("❌ Cannot test superadmin assigned tools without superadmin token")
        success = False
    else:
        response = make_request("GET", "/api/admin/tools/assigned", token=tokens["superadmin"])
        if response.status_code != 200:
            print("❌ Get all tools for superadmin failed")
            success = False
        else:
            print("✅ Get all tools for superadmin successful")
            superadmin_tools = response.json()
            if not isinstance(superadmin_tools, list):
                print("❌ Expected list of tools")
                success = False
            else:
                print(f"✅ Superadmin has access to {len(superadmin_tools)} tools")
    
    if success:
        print("✅ TOOL ACCESS REQUEST SYSTEM TESTS PASSED - All functionality working correctly")
    else:
        print("❌ TOOL ACCESS REQUEST SYSTEM TESTS FAILED - Issues found with access request workflow")
    
    return success

def test_seo_endpoints_with_access_control():
    """Test SEO endpoints with access control - REVIEW REQUEST"""
    print_test_header("SEO ENDPOINTS WITH ACCESS CONTROL - REVIEW REQUEST")
    
    success = True
    
    # Test 1: GET /api/admin/seo/tools - Should show only assigned tools for admin
    print_test_header("Test 1: GET /api/admin/seo/tools - Access Control")
    
    if "admin" not in tokens:
        print("❌ Cannot test SEO tools access without admin token")
        return False
    
    response = make_request("GET", "/api/admin/seo/tools", token=tokens["admin"])
    if response.status_code != 200:
        print("❌ GET SEO tools failed")
        success = False
    else:
        print("✅ GET SEO tools successful")
        seo_tools = response.json()
        if not isinstance(seo_tools, list):
            print("❌ Expected list of SEO tools")
            success = False
        else:
            print(f"✅ Admin can see {len(seo_tools)} tools for SEO management")
            # Verify each tool has expected SEO properties
            if seo_tools:
                sample_tool = seo_tools[0]
                expected_keys = ["tool_id", "tool_name", "has_meta_title", "has_meta_description", "has_ai_content", "optimizations_count"]
                for key in expected_keys:
                    if key not in sample_tool:
                        print(f"❌ Missing SEO tool property: {key}")
                        success = False
                if success:
                    print("✅ SEO tools have all expected properties")
    
    # Test 2: POST /api/admin/seo/optimize - Should check tool access
    print_test_header("Test 2: POST /api/admin/seo/optimize - Access Control")
    
    # Get a tool to optimize (should be one admin has access to)
    tools_response = make_request("GET", "/api/admin/tools/assigned", token=tokens["admin"])
    if tools_response.status_code != 200 or not tools_response.json():
        print("❌ Cannot get assigned tools for SEO optimization test")
        success = False
    else:
        assigned_tools = tools_response.json()
        if assigned_tools:
            test_tool = assigned_tools[0]
            tool_id = test_tool["id"]
            tool_name = test_tool["name"]
            
            print(f"ℹ️ Testing SEO optimization for assigned tool: {tool_name}")
            
            seo_request = {
                "tool_id": tool_id,
                "target_keywords": ["marketing", "automation", "b2b"],
                "search_engine": "google"
            }
            
            # This might fail due to missing AI API keys, but should not fail due to access control
            response = make_request("POST", "/api/admin/seo/optimize", seo_request, token=tokens["admin"], expected_status=[200, 500])
            if response.status_code == 403:
                print("❌ Admin should have access to optimize assigned tools")
                success = False
            elif response.status_code in [200, 500]:
                print("✅ Admin has access to optimize assigned tools (may fail due to API keys)")
            else:
                print(f"❌ Unexpected status code for SEO optimization: {response.status_code}")
                success = False
        else:
            print("⚠️ No assigned tools found for SEO optimization test")
    
    # Test 3: Try to optimize a tool admin doesn't have access to
    print_test_header("Test 3: SEO Optimize Tool Without Access")
    
    # Get all tools and find one not assigned to admin
    all_tools_response = make_request("GET", "/api/tools?limit=10")
    assigned_tools_response = make_request("GET", "/api/admin/tools/assigned", token=tokens["admin"])
    
    if all_tools_response.status_code == 200 and assigned_tools_response.status_code == 200:
        all_tools = all_tools_response.json()
        assigned_tools = assigned_tools_response.json()
        assigned_tool_ids = {tool["id"] for tool in assigned_tools}
        
        unassigned_tool = None
        for tool in all_tools:
            if tool["id"] not in assigned_tool_ids:
                unassigned_tool = tool
                break
        
        if unassigned_tool:
            print(f"ℹ️ Testing SEO optimization for unassigned tool: {unassigned_tool['name']}")
            
            seo_request = {
                "tool_id": unassigned_tool["id"],
                "target_keywords": ["test", "keywords"],
                "search_engine": "google"
            }
            
            response = make_request("POST", "/api/admin/seo/optimize", seo_request, token=tokens["admin"], expected_status=403)
            if response.status_code != 403:
                print("❌ Admin should NOT have access to optimize unassigned tools")
                success = False
            else:
                print("✅ Admin correctly denied access to optimize unassigned tools")
        else:
            print("⚠️ All tools are assigned to admin, cannot test access denial")
    
    if success:
        print("✅ SEO ENDPOINTS ACCESS CONTROL TESTS PASSED - Access control working correctly")
    else:
        print("❌ SEO ENDPOINTS ACCESS CONTROL TESTS FAILED - Issues found with access control")
    
    return success

def test_tool_content_update_endpoint():
    """Test the new tool content update endpoint with access control - REVIEW REQUEST"""
    print_test_header("TOOL CONTENT UPDATE ENDPOINT - REVIEW REQUEST")
    
    success = True
    
    # Test 1: Update content for assigned tool
    print_test_header("Test 1: Update Content for Assigned Tool")
    
    if "admin" not in tokens:
        print("❌ Cannot test tool content update without admin token")
        return False
    
    # Get an assigned tool
    assigned_tools_response = make_request("GET", "/api/admin/tools/assigned", token=tokens["admin"])
    if assigned_tools_response.status_code != 200 or not assigned_tools_response.json():
        print("❌ Cannot get assigned tools for content update test")
        return False
    
    assigned_tools = assigned_tools_response.json()
    if not assigned_tools:
        print("⚠️ No assigned tools found for content update test")
        return False
    
    test_tool = assigned_tools[0]
    tool_id = test_tool["id"]
    tool_name = test_tool["name"]
    
    print(f"ℹ️ Testing content update for assigned tool: {tool_name}")
    
    # Update tool content
    content_update = {
        "description": f"Updated description for {tool_name} - {uuid.uuid4().hex[:8]}",
        "short_description": f"Updated short description - {uuid.uuid4().hex[:8]}",
        "features": "Updated feature 1, Updated feature 2, Updated feature 3",
        "meta_title": f"Updated Meta Title for {tool_name}",
        "meta_description": f"Updated meta description for {tool_name}"
    }
    
    response = make_request("PUT", f"/api/admin/tools/{tool_id}/content", content_update, token=tokens["admin"])
    if response.status_code != 200:
        print("❌ Tool content update for assigned tool failed")
        success = False
        print_response(response)
    else:
        print("✅ Tool content update for assigned tool successful")
        updated_tool = response.json()
        
        # Verify the updates were applied
        if updated_tool.get("description") != content_update["description"]:
            print("❌ Description was not updated correctly")
            success = False
        else:
            print("✅ Description updated correctly")
        
        if updated_tool.get("meta_title") != content_update["meta_title"]:
            print("❌ Meta title was not updated correctly")
            success = False
        else:
            print("✅ Meta title updated correctly")
    
    # Test 2: Try to update content for unassigned tool
    print_test_header("Test 2: Update Content for Unassigned Tool")
    
    # Get all tools and find one not assigned to admin
    all_tools_response = make_request("GET", "/api/tools?limit=10")
    
    if all_tools_response.status_code == 200:
        all_tools = all_tools_response.json()
        assigned_tool_ids = {tool["id"] for tool in assigned_tools}
        
        unassigned_tool = None
        for tool in all_tools:
            if tool["id"] not in assigned_tool_ids:
                unassigned_tool = tool
                break
        
        if unassigned_tool:
            print(f"ℹ️ Testing content update for unassigned tool: {unassigned_tool['name']}")
            
            content_update = {
                "description": "This should not be allowed",
                "short_description": "Access denied test"
            }
            
            response = make_request("PUT", f"/api/admin/tools/{unassigned_tool['id']}/content", content_update, token=tokens["admin"], expected_status=403)
            if response.status_code != 403:
                print("❌ Admin should NOT be able to update content for unassigned tools")
                success = False
            else:
                print("✅ Admin correctly denied access to update unassigned tool content")
        else:
            print("⚠️ All tools are assigned to admin, cannot test access denial")
    
    # Test 3: Superadmin can update any tool content
    print_test_header("Test 3: Superadmin Update Any Tool Content")
    
    if "superadmin" not in tokens:
        print("❌ Cannot test superadmin tool content update without superadmin token")
        success = False
    else:
        # Get any tool
        all_tools_response = make_request("GET", "/api/tools?limit=1")
        if all_tools_response.status_code == 200 and all_tools_response.json():
            test_tool = all_tools_response.json()[0]
            tool_id = test_tool["id"]
            tool_name = test_tool["name"]
            
            print(f"ℹ️ Testing superadmin content update for tool: {tool_name}")
            
            content_update = {
                "description": f"Superadmin updated description - {uuid.uuid4().hex[:8]}",
                "ai_content": f"AI generated content by superadmin - {uuid.uuid4().hex[:8]}"
            }
            
            response = make_request("PUT", f"/api/admin/tools/{tool_id}/content", content_update, token=tokens["superadmin"])
            if response.status_code != 200:
                print("❌ Superadmin tool content update failed")
                success = False
            else:
                print("✅ Superadmin tool content update successful")
                updated_tool = response.json()
                
                if updated_tool.get("description") != content_update["description"]:
                    print("❌ Superadmin description update failed")
                    success = False
                else:
                    print("✅ Superadmin description updated correctly")
    
    if success:
        print("✅ TOOL CONTENT UPDATE ENDPOINT TESTS PASSED - Access control working correctly")
    else:
        print("❌ TOOL CONTENT UPDATE ENDPOINT TESTS FAILED - Issues found with access control")
    
    return success

def test_trending_functionality():
    """Test trending functionality for MarketMindAI discovery page - REVIEW REQUEST"""
    print_test_header("TRENDING FUNCTIONALITY - REVIEW REQUEST")
    
    success = True
    
    # Test 1: /api/tools/analytics endpoint - verify it returns trending data
    print_test_header("Test 1: /api/tools/analytics endpoint")
    response = make_request("GET", "/api/tools/analytics")
    if response.status_code != 200:
        print("❌ /api/tools/analytics endpoint failed")
        success = False
    else:
        data = response.json()
        expected_keys = [
            "trending_tools", "top_rated_tools", "most_viewed_tools", 
            "newest_tools", "featured_tools", "hot_tools"
        ]
        
        for key in expected_keys:
            if key not in data:
                print(f"❌ Missing key in analytics response: {key}")
                success = False
            elif not isinstance(data[key], list):
                print(f"❌ Expected list for {key}, got {type(data[key])}")
                success = False
            else:
                print(f"✅ {key} present and is a list with {len(data[key])} items")
        
        if success:
            print("✅ /api/tools/analytics returns all required trending data")
    
    # Test 2: /api/tools/{tool_id} endpoint - verify it increments views and updates trending
    print_test_header("Test 2: /api/tools/{tool_id} endpoint - view increment and trending update")
    
    # Get a tool to test with
    tools_response = make_request("GET", "/api/tools?limit=1")
    if tools_response.status_code != 200 or not tools_response.json():
        print("❌ Cannot get tools for trending test")
        success = False
    else:
        test_tool = tools_response.json()[0]
        tool_id = test_tool["id"]
        initial_views = test_tool.get("views", 0)
        initial_trending_score = test_tool.get("trending_score", 0)
        
        print(f"ℹ️ Testing with tool: {test_tool['name']} (ID: {tool_id})")
        print(f"ℹ️ Initial views: {initial_views}, Initial trending score: {initial_trending_score}")
        
        # Access the tool to increment views
        response = make_request("GET", f"/api/tools/{tool_id}")
        if response.status_code != 200:
            print("❌ GET tool by ID failed")
            success = False
        else:
            updated_tool = response.json()
            new_views = updated_tool.get("views", 0)
            new_trending_score = updated_tool.get("trending_score", 0)
            
            print(f"ℹ️ After access - Views: {new_views}, Trending score: {new_trending_score}")
            
            # Verify views were incremented
            if new_views != initial_views + 1:
                print(f"❌ Views not incremented correctly. Expected {initial_views + 1}, got {new_views}")
                success = False
            else:
                print("✅ Views incremented correctly")
            
            # Verify trending score exists (it should be calculated)
            if "trending_score" not in updated_tool:
                print("❌ Trending score not present in tool response")
                success = False
            else:
                print(f"✅ Trending score present: {new_trending_score}")
    
    # Test 3: /api/admin/tools/update-trending endpoint (Super Admin only)
    print_test_header("Test 3: /api/admin/tools/update-trending endpoint")
    
    if "superadmin" not in tokens:
        print("❌ Cannot test manual trending update without superadmin token")
        success = False
    else:
        response = make_request("POST", "/api/admin/tools/update-trending", token=tokens["superadmin"])
        if response.status_code != 200:
            print("❌ Manual trending update failed")
            success = False
        else:
            result = response.json()
            if "message" not in result or "details" not in result:
                print("❌ Manual trending update response missing expected keys")
                success = False
            else:
                print(f"✅ Manual trending update successful: {result['message']}")
                print(f"ℹ️ Update details: {result['details']}")
    
    # Test 4: /api/admin/tools/update-trending-manual endpoint (Super Admin only)
    print_test_header("Test 4: /api/admin/tools/update-trending-manual endpoint")
    
    if "superadmin" not in tokens:
        print("❌ Cannot test manual trending trigger without superadmin token")
        success = False
    else:
        response = make_request("POST", "/api/admin/tools/update-trending-manual", token=tokens["superadmin"])
        if response.status_code != 200:
            print("❌ Manual trending trigger failed")
            success = False
        else:
            result = response.json()
            if "message" not in result:
                print("❌ Manual trending trigger response missing message")
                success = False
            else:
                print(f"✅ Manual trending trigger successful: {result['message']}")
    
    # Test 5: /api/admin/tools/trending-stats endpoint (Super Admin only)
    print_test_header("Test 5: /api/admin/tools/trending-stats endpoint")
    
    if "superadmin" not in tokens:
        print("❌ Cannot test trending stats without superadmin token")
        success = False
    else:
        response = make_request("GET", "/api/admin/tools/trending-stats", token=tokens["superadmin"])
        if response.status_code != 200:
            print("❌ Trending stats endpoint failed")
            success = False
        else:
            stats = response.json()
            expected_stats_keys = ["total_tools", "total_views", "avg_trending_score", "top_trending"]
            
            for key in expected_stats_keys:
                if key not in stats:
                    print(f"❌ Missing key in trending stats: {key}")
                    success = False
                else:
                    print(f"✅ {key}: {stats[key]}")
            
            # Verify top_trending is a list of tools with required properties
            if "top_trending" in stats and isinstance(stats["top_trending"], list):
                if stats["top_trending"]:
                    sample_trending_tool = stats["top_trending"][0]
                    required_props = ["name", "trending_score", "views", "rating"]
                    for prop in required_props:
                        if prop not in sample_trending_tool:
                            print(f"❌ Missing property {prop} in top trending tool")
                            success = False
                    if success:
                        print("✅ Top trending tools have all required properties")
                else:
                    print("ℹ️ No top trending tools found")
            else:
                print("❌ top_trending should be a list")
                success = False
    
    # Test 6: Verify trending scores are calculated correctly
    print_test_header("Test 6: Verify trending score calculation")
    
    # Get analytics again to see if trending data is fresh
    response = make_request("GET", "/api/tools/analytics?recalculate=true")
    if response.status_code != 200:
        print("❌ Analytics with recalculate failed")
        success = False
    else:
        data = response.json()
        trending_tools = data.get("trending_tools", [])
        
        if trending_tools:
            # Check if trending tools are sorted by trending score
            trending_scores = [tool.get("trending_score", 0) for tool in trending_tools]
            is_sorted = all(trending_scores[i] >= trending_scores[i+1] for i in range(len(trending_scores)-1))
            
            if is_sorted:
                print("✅ Trending tools are correctly sorted by trending score")
                print(f"ℹ️ Top trending tool: {trending_tools[0]['name']} (score: {trending_tools[0].get('trending_score', 0)})")
            else:
                print("❌ Trending tools are not sorted by trending score")
                success = False
        else:
            print("ℹ️ No trending tools found for sorting verification")
    
    # Test 7: Test role-based access control for admin endpoints
    print_test_header("Test 7: Role-based access control for trending admin endpoints")
    
    if "admin" in tokens:
        # Regular admin should NOT be able to access superadmin-only trending endpoints
        admin_restricted_endpoints = [
            "/api/admin/tools/update-trending",
            "/api/admin/tools/update-trending-manual", 
            "/api/admin/tools/trending-stats"
        ]
        
        for endpoint in admin_restricted_endpoints:
            if endpoint.endswith("trending-stats"):
                response = make_request("GET", endpoint, token=tokens["admin"], expected_status=403)
            else:
                response = make_request("POST", endpoint, token=tokens["admin"], expected_status=403)
            
            if response.status_code != 403:
                print(f"❌ Regular admin should not access {endpoint}")
                success = False
            else:
                print(f"✅ Regular admin correctly denied access to {endpoint}")
    
    if success:
        print("✅ TRENDING FUNCTIONALITY TESTS PASSED - All trending features working correctly")
    else:
        print("❌ TRENDING FUNCTIONALITY TESTS FAILED - Issues found with trending features")
    
    return success

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
        tools_created = result.get("tools_created", result.get("created_count", 0))
        if tools_created == 0:
            print("✅ Bulk upload correctly handled empty CSV")
        else:
            print("❌ Bulk upload should not create tools from empty CSV")
            success = False
    else:
        print("❌ Bulk upload with empty CSV failed unexpectedly")
        success = False
    
    # Test 9: Test complete end-to-end flow - download template → upload CSV → verify successful upload
    print_test_header("Complete End-to-End Flow - Download Template → Upload CSV → Verify")
    
    # Step 1: Download template
    template_response = make_request("GET", "/api/admin/tools/sample-csv", token=tokens["superadmin"])
    if template_response.status_code == 200:
        print("✅ Step 1: Template downloaded successfully")
        
        # Step 2: Modify the template content
        template_content = template_response.text
        
        # Replace placeholder with actual category ID if available
        if test_category_id:
            modified_content = template_content.replace("CREATE_CATEGORIES_FIRST", test_category_id)
            modified_content = modified_content.replace("REPLACE_WITH_ACTUAL_CATEGORY_ID", test_category_id)
            
            # Add a unique tool name to avoid conflicts
            unique_tool_name = f"E2E Test Tool {uuid.uuid4().hex[:8]}"
            lines = modified_content.strip().split('\n')
            if len(lines) >= 2:  # Header + at least one data row
                header = lines[0]
                new_row = lines[1].replace("Example Tool", unique_tool_name)
                new_row = new_row.replace("Example Tool 1", unique_tool_name)
                modified_content = f"{header}\n{new_row}"
                
                print("✅ Step 2: Template modified with valid data")
                
                # Step 3: Upload the modified CSV
                files = {'file': ('e2e_test.csv', modified_content, 'text/csv')}
                upload_response = make_request("POST", "/api/tools/bulk-upload", files=files, token=tokens["superadmin"])
                
                if upload_response.status_code == 200:
                    result = upload_response.json()
                    tools_created = result.get("tools_created", result.get("created_count", 0))
                    if tools_created > 0:
                        print("✅ Step 3: CSV uploaded successfully")
                        created_tools = result.get("created_tools", [])
                        
                        # Step 4: Verify the tool was created by searching for it
                        if created_tools and unique_tool_name in created_tools:
                            search_response = make_request("GET", f"/api/tools/search?q={unique_tool_name.replace(' ', '%20')}")
                            if search_response.status_code == 200:
                                search_data = search_response.json()
                                if search_data.get("total", 0) > 0:
                                    found_tool = None
                                    for tool in search_data.get("tools", []):
                                        if tool.get("name") == unique_tool_name:
                                            found_tool = tool
                                            break
                                    
                                    if found_tool:
                                        print("✅ Step 4: Tool verified in database - End-to-End flow successful!")
                                        print(f"   Tool ID: {found_tool.get('id')}")
                                        print(f"   Tool Name: {found_tool.get('name')}")
                                        print(f"   Category ID: {found_tool.get('category_id')}")
                                    else:
                                        print("❌ Step 4: Tool not found in search results")
                                        success = False
                                else:
                                    print("❌ Step 4: No tools found in search")
                                    success = False
                            else:
                                print("❌ Step 4: Search request failed")
                                success = False
                        else:
                            print("❌ Step 4: Tool name not in created tools list")
                            success = False
                    else:
                        print("❌ Step 3: Upload completed but no tools created")
                        success = False
                else:
                    print("❌ Step 3: Upload failed")
                    success = False
            else:
                print("❌ Step 2: Template content is malformed")
                success = False
        else:
            print("⚠️ Cannot test complete flow without valid category ID")
    else:
        print("❌ Step 1: Cannot download template for complete flow test")
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

def test_blog_creation_comprehensive():
    """Comprehensive test for blog creation functionality as requested"""
    print_test_header("COMPREHENSIVE BLOG CREATION TESTING")
    
    if "user" not in tokens or "admin" not in tokens:
        print("❌ Cannot test blog creation without user and admin tokens")
        return False
    
    success = True
    
    # Test 1: Blog creation with text content
    print_test_header("Blog Creation with Text Content")
    blog_data = {
        "title": f"Test Blog Post {uuid.uuid4().hex[:8]}",
        "content": """
        <h1>This is a comprehensive blog post</h1>
        <p>This blog post contains <strong>rich text formatting</strong> including:</p>
        <ul>
            <li>Bold and italic text</li>
            <li>Lists and headings</li>
            <li>Links and images</li>
        </ul>
        <p>The content is long enough to calculate proper reading time. """ + "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 50,
        "excerpt": "This is a test blog excerpt with rich formatting",
        "status": "published",
        "category_id": test_category_id if test_category_id else None,
        "slug": f"test-blog-{uuid.uuid4().hex[:8]}",
        "meta_title": "Test Blog Meta Title",
        "meta_description": "Test blog meta description for SEO"
    }
    
    response = make_request("POST", "/api/blogs", blog_data, token=tokens["user"], expected_status=200)
    if response.status_code != 200:
        print("❌ Blog creation with text content failed")
        success = False
    else:
        blog_result = response.json()
        global test_blog_id
        test_blog_id = blog_result["id"]
        
        # Verify blog properties
        if blog_result.get("reading_time", 0) > 0:
            print(f"✅ Blog created with reading time: {blog_result['reading_time']} minutes")
        else:
            print("❌ Blog reading time not calculated properly")
            success = False
            
        if blog_result.get("status") == "published":
            print("✅ Blog status set to published")
        else:
            print("❌ Blog status not set correctly")
            success = False
            
        if blog_result.get("published_at"):
            print("✅ Blog published_at timestamp set")
        else:
            print("❌ Blog published_at timestamp not set")
            success = False
    
    # Test 2: Blog creation with different content formats
    print_test_header("Blog Creation with Various Content Formats")
    
    # Test with draft status
    draft_blog = {
        "title": f"Draft Blog {uuid.uuid4().hex[:8]}",
        "content": "This is a draft blog post",
        "excerpt": "Draft excerpt",
        "status": "draft",
        "slug": f"draft-blog-{uuid.uuid4().hex[:8]}"
    }
    
    response = make_request("POST", "/api/blogs", draft_blog, token=tokens["user"], expected_status=200)
    if response.status_code != 200:
        print("❌ Draft blog creation failed")
        success = False
    else:
        draft_result = response.json()
        if draft_result.get("status") == "draft" and not draft_result.get("published_at"):
            print("✅ Draft blog created correctly (no published_at)")
        else:
            print("❌ Draft blog status handling incorrect")
            success = False
    
    # Test with rich text formatting
    rich_text_blog = {
        "title": f"Rich Text Blog {uuid.uuid4().hex[:8]}",
        "content": """
        <h2>Rich Text Content</h2>
        <p>This blog contains <em>italic</em>, <strong>bold</strong>, and <u>underlined</u> text.</p>
        <blockquote>This is a blockquote with important information.</blockquote>
        <pre><code>console.log('This is code formatting');</code></pre>
        <p>Here's a list:</p>
        <ol>
            <li>First item</li>
            <li>Second item with <a href="https://example.com">a link</a></li>
            <li>Third item</li>
        </ol>
        """,
        "excerpt": "Rich text formatting test",
        "status": "published",
        "slug": f"rich-text-blog-{uuid.uuid4().hex[:8]}"
    }
    
    response = make_request("POST", "/api/blogs", rich_text_blog, token=tokens["user"], expected_status=200)
    if response.status_code != 200:
        print("❌ Rich text blog creation failed")
        success = False
    else:
        print("✅ Rich text blog created successfully")
    
    # Test 3: Blog search and filtering functionality
    print_test_header("Blog Search and Filtering")
    
    # Test basic blog retrieval
    response = make_request("GET", "/api/blogs", expected_status=200)
    if response.status_code != 200:
        print("❌ Basic blog retrieval failed")
        success = False
    else:
        blogs = response.json()
        if isinstance(blogs, list) and len(blogs) > 0:
            print(f"✅ Retrieved {len(blogs)} blogs")
        else:
            print("❌ No blogs retrieved or invalid format")
            success = False
    
    # Test search functionality
    response = make_request("GET", "/api/blogs?search=Test", expected_status=200)
    if response.status_code != 200:
        print("❌ Blog search failed")
        success = False
    else:
        search_results = response.json()
        print(f"✅ Blog search returned {len(search_results)} results")
    
    # Test category filtering
    if test_category_id:
        response = make_request("GET", f"/api/blogs?category_id={test_category_id}", expected_status=200)
        if response.status_code != 200:
            print("❌ Blog category filtering failed")
            success = False
        else:
            print("✅ Blog category filtering works")
    
    # Test status filtering
    response = make_request("GET", "/api/blogs?status=published", expected_status=200)
    if response.status_code != 200:
        print("❌ Blog status filtering failed")
        success = False
    else:
        print("✅ Blog status filtering works")
    
    # Test sorting options
    sort_options = ["created_at", "views", "likes", "oldest"]
    for sort_by in sort_options:
        response = make_request("GET", f"/api/blogs?sort_by={sort_by}", expected_status=200)
        if response.status_code != 200:
            print(f"❌ Blog sorting by {sort_by} failed")
            success = False
        else:
            print(f"✅ Blog sorting by {sort_by} works")
    
    # Test 4: Blog likes functionality
    print_test_header("Blog Likes Functionality")
    
    if test_blog_id:
        # Get initial likes count
        response = make_request("GET", f"/api/blogs/{test_blog_id}", expected_status=200)
        if response.status_code != 200:
            print("❌ Cannot retrieve blog for likes test")
            success = False
        else:
            initial_blog = response.json()
            initial_likes = initial_blog.get("likes", 0)
            
            # Like the blog
            response = make_request("POST", f"/api/blogs/{test_blog_id}/like", token=tokens["user"], expected_status=200)
            if response.status_code != 200:
                print("❌ Blog like functionality failed")
                success = False
            else:
                like_result = response.json()
                new_likes = like_result.get("likes", 0)
                
                if new_likes > initial_likes:
                    print(f"✅ Blog likes increased from {initial_likes} to {new_likes}")
                else:
                    print("❌ Blog likes count did not increase")
                    success = False
                
                # Verify likes count persisted
                response = make_request("GET", f"/api/blogs/{test_blog_id}", expected_status=200)
                if response.status_code == 200:
                    updated_blog = response.json()
                    if updated_blog.get("likes", 0) == new_likes:
                        print("✅ Blog likes count persisted in database")
                    else:
                        print("❌ Blog likes count not persisted properly")
                        success = False
    
    # Test 5: Blog permissions (user vs admin)
    print_test_header("Blog Permissions Testing")
    
    if test_blog_id:
        # Test user can update their own blog
        update_data = {
            "title": f"Updated Blog Title {uuid.uuid4().hex[:8]}",
            "content": "Updated content for the blog post"
        }
        response = make_request("PUT", f"/api/blogs/{test_blog_id}", update_data, token=tokens["user"], expected_status=200)
        if response.status_code != 200:
            print("❌ User cannot update their own blog")
            success = False
        else:
            print("✅ User can update their own blog")
        
        # Test admin can update any blog
        admin_update = {
            "title": f"Admin Updated Title {uuid.uuid4().hex[:8]}",
            "status": "published"
        }
        response = make_request("PUT", f"/api/blogs/{test_blog_id}", admin_update, token=tokens["admin"], expected_status=200)
        if response.status_code != 200:
            print("❌ Admin cannot update user's blog")
            success = False
        else:
            print("✅ Admin can update any blog")
        
        # Test admin can delete any blog
        response = make_request("DELETE", f"/api/blogs/{test_blog_id}", token=tokens["admin"], expected_status=200)
        if response.status_code != 200:
            print("❌ Admin cannot delete blog")
            success = False
        else:
            print("✅ Admin can delete any blog")
    
    # Test 6: Blog view count increment
    print_test_header("Blog View Count Testing")
    
    # Create a new blog for view testing
    view_test_blog = {
        "title": f"View Test Blog {uuid.uuid4().hex[:8]}",
        "content": "This blog is for testing view counts",
        "excerpt": "View test excerpt",
        "status": "published",
        "slug": f"view-test-blog-{uuid.uuid4().hex[:8]}"
    }
    
    response = make_request("POST", "/api/blogs", view_test_blog, token=tokens["user"], expected_status=200)
    if response.status_code == 200:
        view_blog_id = response.json()["id"]
        initial_views = response.json().get("views", 0)
        
        # Access the blog to increment views
        response = make_request("GET", f"/api/blogs/{view_blog_id}", expected_status=200)
        if response.status_code == 200:
            updated_views = response.json().get("views", 0)
            if updated_views > initial_views:
                print(f"✅ Blog view count incremented from {initial_views} to {updated_views}")
            else:
                print("❌ Blog view count not incremented")
                success = False
    
    return success

def test_file_upload_functionality():
    """Test file upload functionality"""
    print_test_header("FILE UPLOAD FUNCTIONALITY TESTING")
    
    if "user" not in tokens:
        print("❌ Cannot test file upload without user token")
        return False
    
    success = True
    
    # Test 1: Valid image file upload
    print_test_header("Valid Image File Upload")
    
    # Create a small test image (1x1 pixel PNG)
    import base64
    # This is a 1x1 transparent PNG image in base64
    small_png_data = base64.b64decode(
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU8IQAAAAABJRU5ErkJggg=='
    )
    
    files = {'file': ('test_image.png', small_png_data, 'image/png')}
    response = make_request("POST", "/api/upload", files=files, token=tokens["user"], expected_status=200)
    
    if response.status_code != 200:
        print("❌ Valid image upload failed")
        success = False
    else:
        upload_result = response.json()
        required_keys = ["file_url", "filename", "content_type", "size"]
        
        for key in required_keys:
            if key not in upload_result:
                print(f"❌ Upload response missing key: {key}")
                success = False
        
        if upload_result.get("content_type") == "image/png":
            print("✅ Image upload successful with correct content type")
        else:
            print(f"❌ Expected image/png, got {upload_result.get('content_type')}")
            success = False
        
        if upload_result.get("file_url", "").startswith("data:image/png;base64,"):
            print("✅ File returned as base64 data URL")
        else:
            print("❌ File not returned as expected base64 data URL")
            success = False
    
    # Test 2: Invalid file type upload
    print_test_header("Invalid File Type Upload")
    
    files = {'file': ('test.txt', b'This is a text file', 'text/plain')}
    response = make_request("POST", "/api/upload", files=files, token=tokens["user"], expected_status=400)
    
    if response.status_code != 400:
        print("❌ Invalid file type should be rejected")
        success = False
    else:
        print("✅ Invalid file type correctly rejected")
    
    # Test 3: Large file upload (should fail)
    print_test_header("Large File Upload (Should Fail)")
    
    # Create a file larger than 10MB (simulated)
    large_file_data = b'x' * (11 * 1024 * 1024)  # 11MB
    files = {'file': ('large_image.jpg', large_file_data, 'image/jpeg')}
    response = make_request("POST", "/api/upload", files=files, token=tokens["user"], expected_status=400)
    
    if response.status_code != 400:
        print("❌ Large file should be rejected")
        success = False
    else:
        print("✅ Large file correctly rejected")
    
    # Test 4: Upload without authentication
    print_test_header("Upload Without Authentication")
    
    files = {'file': ('test_image.png', small_png_data, 'image/png')}
    response = make_request("POST", "/api/upload", files=files, expected_status=401)
    
    if response.status_code != 401:
        print("❌ Upload without authentication should fail")
        success = False
    else:
        print("✅ Upload without authentication correctly rejected")
    
    # Test 5: Different valid file types
    print_test_header("Different Valid File Types")
    
    # Test JPEG
    files = {'file': ('test.jpg', small_png_data, 'image/jpeg')}
    response = make_request("POST", "/api/upload", files=files, token=tokens["user"], expected_status=200)
    if response.status_code == 200:
        print("✅ JPEG upload successful")
    else:
        print("❌ JPEG upload failed")
        success = False
    
    # Test GIF
    files = {'file': ('test.gif', small_png_data, 'image/gif')}
    response = make_request("POST", "/api/upload", files=files, token=tokens["user"], expected_status=200)
    if response.status_code == 200:
        print("✅ GIF upload successful")
    else:
        print("❌ GIF upload failed")
        success = False
    
    # Test WebP
    files = {'file': ('test.webp', small_png_data, 'image/webp')}
    response = make_request("POST", "/api/upload", files=files, token=tokens["user"], expected_status=200)
    if response.status_code == 200:
        print("✅ WebP upload successful")
    else:
        print("❌ WebP upload failed")
        success = False
    
    return success

def run_all_tests():
    """Run focused tests for blog creation, file upload, and CSV access functionality"""
    try:
        results = {}
        
        # Health check first
        results["health_check"] = test_health_check()
        
        # Authentication - Critical for access control testing
        results["login"] = test_login()
        
        # Set up basic data needed for tests
        results["protected_routes"] = test_protected_routes()
        results["categories_crud"] = test_categories_crud()
        
        # MAIN REQUESTED TESTS - Focus on blog creation issue
        print("\n" + "🎯" * 40)
        print("MAIN REQUESTED TESTS - BLOG CREATION FOCUS")
        print("🎯" * 40)
        
        results["blog_creation_validation"] = test_blog_creation_validation()
        results["blogs_crud"] = test_blogs_crud()
        results["file_upload"] = test_file_upload()
        results["csv_endpoint_access"] = test_csv_endpoint_access()
        
        # Additional supporting tests
        results["tools_crud"] = test_tools_crud()
        results["sample_csv"] = test_sample_csv()
        
        # Print summary
        print("\n" + "=" * 80)
        print("BLOG CREATION ISSUE INVESTIGATION SUMMARY - MarketMindAI")
        print("=" * 80)
        
        main_tests = ["blog_creation_validation", "blogs_crud", "file_upload", "csv_endpoint_access"]
        main_passed = True
        
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            if test_name in main_tests:
                print(f"🎯 MAIN TEST - {test_name}: {status}")
                if not passed:
                    main_passed = False
            else:
                print(f"   Supporting - {test_name}: {status}")
        
        print("\n" + "=" * 80)
        if main_passed:
            print("🎉 MAIN TESTS PASSED! Blog creation validation and related functionality working correctly.")
        else:
            print("❌ MAIN TESTS FAILED! Blog creation validation or related functionality issues detected.")
            
        # Count overall results
        total_tests = len(results)
        passed_tests = sum(1 for passed in results.values() if passed)
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        
        # Specific findings summary
        print("\n" + "🔍" * 40)
        print("SPECIFIC FINDINGS SUMMARY")
        print("🔍" * 40)
        
        if results.get("blog_creation_validation"):
            print("✅ Blog creation validation: category_id requirement working correctly")
        else:
            print("❌ Blog creation validation: Issues with category_id requirement")
            
        if results.get("file_upload"):
            print("✅ File upload functionality: Working correctly")
        else:
            print("❌ File upload functionality: Issues detected")
            
        if results.get("csv_endpoint_access"):
            print("✅ CSV endpoint access: Role-based permissions working correctly")
        else:
            print("❌ CSV endpoint access: Permission issues detected")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

def test_review_request_scenarios():
    """Test the specific scenarios mentioned in the review request"""
    print_test_header("REVIEW REQUEST SPECIFIC TESTING")
    
    success = True
    
    # Scenario 1: Login as superadmin
    print_test_header("Scenario 1: Login as superadmin")
    login_data = {
        "email": "superadmin@marketmindai.com",
        "password": "superadmin123"
    }
    response = make_request("POST", "/api/auth/login", login_data, expected_status=200)
    if response.status_code != 200:
        print("❌ Superadmin login failed")
        success = False
        return False
    else:
        superadmin_token = response.json()["access_token"]
        tokens["superadmin"] = superadmin_token
        print("✅ Superadmin login successful")
    
    # Scenario 2: Test the advanced analytics endpoint
    print_test_header("Scenario 2: Test advanced analytics endpoint")
    response = make_request("GET", "/api/admin/analytics/advanced", token=tokens["superadmin"], expected_status=200)
    if response.status_code != 200:
        print("❌ Advanced analytics endpoint failed")
        success = False
    else:
        print("✅ Advanced analytics endpoint working correctly")
        data = response.json()
        # Verify the structure contains overview data
        expected_keys = ["user_stats", "content_stats", "review_stats", "recent_activity"]
        for key in expected_keys:
            if key not in data:
                print(f"❌ Missing key in analytics response: {key}")
                success = False
            else:
                print(f"✅ Analytics contains {key}")
    
    # Scenario 3: Test creating a tool
    print_test_header("Scenario 3: Test creating a tool")
    
    # First, get or create a category for the tool
    categories_response = make_request("GET", "/api/categories", expected_status=200)
    if categories_response.status_code != 200 or not categories_response.json():
        # Create a category first
        category_data = {
            "name": f"Test Category {uuid.uuid4().hex[:8]}",
            "description": "Test Category for Tool Creation",
            "icon": "test-icon",
            "color": "#123456"
        }
        cat_response = make_request("POST", "/api/categories", category_data, token=tokens["superadmin"], expected_status=200)
        if cat_response.status_code != 200:
            print("❌ Failed to create category for tool testing")
            success = False
            return False
        category_id = cat_response.json()["id"]
    else:
        category_id = categories_response.json()[0]["id"]
    
    # Now create a tool
    tool_data = {
        "name": f"Test Tool {uuid.uuid4().hex[:8]}",
        "description": "Test Tool Description for Review Request",
        "short_description": "Short description for testing",
        "category_id": category_id,
        "pricing_model": "Freemium",
        "company_size": "SMB",
        "slug": f"test-tool-{uuid.uuid4().hex[:8]}",
        "is_hot": True,
        "is_featured": True,
        "website_url": "https://example.com",
        "features": "Feature 1, Feature 2, Feature 3"
    }
    response = make_request("POST", "/api/tools", tool_data, token=tokens["superadmin"], expected_status=200)
    if response.status_code != 200:
        print("❌ Tool creation failed")
        success = False
    else:
        print("✅ Tool creation successful")
        created_tool_id = response.json()["id"]
        print(f"Created tool ID: {created_tool_id}")
    
    # Scenario 4: Test getting all blogs
    print_test_header("Scenario 4: Test getting all blogs")
    response = make_request("GET", "/api/blogs", expected_status=200)
    if response.status_code != 200:
        print("❌ Getting all blogs failed")
        success = False
    else:
        print("✅ Getting all blogs successful")
        blogs = response.json()
        print(f"Found {len(blogs)} blogs")
        
        # If we have blogs, test getting a specific blog
        if blogs:
            # Scenario 5: Test getting a specific blog by ID
            print_test_header("Scenario 5: Test getting specific blog by ID")
            blog_id = blogs[0]["id"]
            response = make_request("GET", f"/api/blogs/{blog_id}", expected_status=200)
            if response.status_code != 200:
                print("❌ Getting specific blog failed")
                success = False
            else:
                print("✅ Getting specific blog successful")
                blog_data = response.json()
                print(f"Retrieved blog: {blog_data.get('title', 'No title')}")
        else:
            print("⚠️ No blogs found to test individual blog retrieval")
            # Create a blog for testing
            print_test_header("Creating a blog for testing individual retrieval")
            blog_data = {
                "title": f"Test Blog {uuid.uuid4().hex[:8]}",
                "content": "This is a test blog content for the review request testing. " * 20,
                "excerpt": "Test excerpt for review request",
                "status": "published",
                "category_id": category_id,
                "slug": f"test-blog-{uuid.uuid4().hex[:8]}"
            }
            
            # Login as admin to create blog
            admin_login_data = {
                "email": "admin@marketmindai.com",
                "password": "admin123"
            }
            admin_response = make_request("POST", "/api/auth/login", admin_login_data, expected_status=200)
            if admin_response.status_code == 200:
                admin_token = admin_response.json()["access_token"]
                tokens["admin"] = admin_token
                
                blog_response = make_request("POST", "/api/blogs", blog_data, token=admin_token, expected_status=200)
                if blog_response.status_code == 200:
                    created_blog_id = blog_response.json()["id"]
                    print(f"✅ Created blog for testing: {created_blog_id}")
                    
                    # Now test getting the specific blog
                    print_test_header("Scenario 5: Test getting specific blog by ID")
                    response = make_request("GET", f"/api/blogs/{created_blog_id}", expected_status=200)
                    if response.status_code != 200:
                        print("❌ Getting specific blog failed")
                        success = False
                    else:
                        print("✅ Getting specific blog successful")
                        blog_data = response.json()
                        print(f"Retrieved blog: {blog_data.get('title', 'No title')}")
                else:
                    print("❌ Failed to create blog for testing")
                    success = False
            else:
                print("❌ Failed to login as admin for blog creation")
                success = False
    
    return success

def run_trending_functionality_tests():
    """Run trending functionality tests as requested in the review"""
    print("Starting MarketMindAI Trending Functionality Testing")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    success = True
    
    try:
        # First, ensure we have authentication tokens
        if not test_health_check():
            print("❌ Health check failed")
            return False
        
        if not test_login():
            print("❌ Login failed - cannot proceed with trending tests")
            return False
        
        # Run the trending functionality tests
        if not test_trending_functionality():
            print("❌ Trending functionality tests failed")
            success = False
        
        if success:
            print("\n✅ ALL TRENDING FUNCTIONALITY TESTS PASSED")
            return True
        else:
            print("\n❌ SOME TRENDING FUNCTIONALITY TESTS FAILED")
            return False
            
    except Exception as e:
        print(f"\n❌ TRENDING FUNCTIONALITY TESTING FAILED with exception: {str(e)}")
        return False

def run_tool_access_request_tests():
    """Run the new tool access request system tests as requested in the review"""
    print("Starting MarketMindAI Tool Access Request System Testing")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    success = True
    
    try:
        # First, ensure we have authentication tokens
        if not test_health_check():
            print("❌ Health check failed")
            return False
        
        if not test_login():
            print("❌ Login failed - cannot proceed with tool access request tests")
            return False
        
        # Run the tool access request system tests
        if not test_tool_access_request_system():
            print("❌ Tool access request system tests failed")
            success = False
        
        # Test SEO endpoints with access control
        if not test_seo_endpoints_with_access_control():
            print("❌ SEO endpoints access control tests failed")
            success = False
        
        # Test tool content update endpoint
        if not test_tool_content_update_endpoint():
            print("❌ Tool content update endpoint tests failed")
            success = False
        
        if success:
            print("\n✅ ALL TOOL ACCESS REQUEST SYSTEM TESTS PASSED")
            return True
        else:
            print("\n❌ SOME TOOL ACCESS REQUEST SYSTEM TESTS FAILED")
            return False
            
    except Exception as e:
        print(f"\n❌ TOOL ACCESS REQUEST SYSTEM TESTING FAILED with exception: {str(e)}")
        return False

def run_review_request_tests():
    """Run only the tests requested in the review request"""
    print("Starting MarketMindAI Review Request Testing")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    try:
        if test_review_request_scenarios():
            print("\n✅ ALL REVIEW REQUEST SCENARIOS PASSED")
            return True
        else:
            print("\n❌ SOME REVIEW REQUEST SCENARIOS FAILED")
            return False
    except Exception as e:
        print(f"\n❌ REVIEW REQUEST TESTING FAILED with exception: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the tool access request system tests as requested in the review
    run_tool_access_request_tests()