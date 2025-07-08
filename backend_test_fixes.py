import requests
import json
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# Get backend URL from environment
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "http://localhost:8001")

# Seeded users for testing
SEEDED_USERS = [
    {"email": "user@marketmindai.com", "password": "password123", "type": "user"},
    {"email": "admin@marketmindai.com", "password": "admin123", "type": "admin"},
    {"email": "superadmin@marketmindai.com", "password": "superadmin123", "type": "superadmin"}
]

# Store tokens and test IDs
tokens = {}
test_category_id = None
test_tool_id = None

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
    data=None,
    token=None,
    expected_status=200,
    params=None,
    files=None,
    json_data=True
):
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
        elif json_data:
            response = requests.post(url, json=data, headers=headers, params=params)
        else:
            response = requests.post(url, data=data, headers=headers, params=params)
    elif method.lower() == "put":
        if json_data:
            response = requests.put(url, json=data, headers=headers, params=params)
        else:
            response = requests.put(url, data=data, headers=headers, params=params)
    elif method.lower() == "delete":
        response = requests.delete(url, headers=headers, params=params)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    
    print_response(response)
    
    if isinstance(expected_status, list):
        if response.status_code not in expected_status:
            print(f"❌ Expected status code in {expected_status}, got {response.status_code}")
        else:
            print(f"✅ Status code {response.status_code} as expected")
    else:
        if response.status_code != expected_status:
            print(f"❌ Expected status code {expected_status}, got {response.status_code}")
        else:
            print(f"✅ Status code {expected_status} as expected")
    
    return response

def login_users():
    """Login with seeded users and store tokens"""
    print_test_header("Login Users")
    
    for user in SEEDED_USERS:
        login_data = {
            "email": user["email"],
            "password": user["password"]
        }
        response = make_request("POST", "/api/auth/login", login_data)
        if response.status_code == 200:
            tokens[user["type"]] = response.json()["access_token"]
            print(f"✅ Logged in as {user['type']}")
        else:
            print(f"❌ Failed to login as {user['type']}")
    
    return len(tokens) == len(SEEDED_USERS)

def create_test_category():
    """Create a test category for testing"""
    print_test_header("Create Test Category")
    
    if "admin" not in tokens:
        print("❌ Cannot create test category without admin token")
        return False
    
    category_data = {
        "name": f"Test Category {uuid.uuid4().hex[:8]}",
        "description": "Test Description",
        "icon": "test-icon",
        "color": "#123456"
    }
    
    response = make_request("POST", "/api/categories", category_data, token=tokens["admin"])
    if response.status_code == 200:
        global test_category_id
        test_category_id = response.json()["id"]
        print(f"✅ Created test category with ID: {test_category_id}")
        return True
    else:
        print("❌ Failed to create test category")
        return False

def create_test_tool():
    """Create a test tool for testing"""
    print_test_header("Create Test Tool")
    
    if "admin" not in tokens or not test_category_id:
        print("❌ Cannot create test tool without admin token or category ID")
        return False
    
    tool_data = {
        "name": f"Test Tool {uuid.uuid4().hex[:8]}",
        "description": "Test Tool Description",
        "short_description": "Short description",
        "category_id": test_category_id,
        "pricing_model": "Freemium",
        "company_size": "SMB",
        "slug": f"test-tool-{uuid.uuid4().hex[:8]}",
        "is_hot": True,
        "is_featured": True
    }
    
    response = make_request("POST", "/api/tools", tool_data, token=tokens["admin"])
    if response.status_code == 200:
        global test_tool_id
        test_tool_id = response.json()["id"]
        print(f"✅ Created test tool with ID: {test_tool_id}")
        return True
    else:
        print("❌ Failed to create test tool")
        return False

def test_authentication_status_codes():
    """Test that authentication errors return 401 status codes"""
    print_test_header("Authentication Status Codes")
    
    # Test accessing protected route without token
    response = make_request("GET", "/api/auth/me", expected_status=401)
    if response.status_code != 401:
        print("❌ Accessing protected route without token should return 401")
        return False
    
    # Test with invalid token
    invalid_token = "invalid.token.here"
    response = make_request("GET", "/api/auth/me", token=invalid_token, expected_status=401)
    if response.status_code != 401:
        print("❌ Accessing protected route with invalid token should return 401")
        return False
    
    # Test with malformed token
    headers = {"Authorization": "Bearer"}
    url = f"{BACKEND_URL}/api/auth/me"
    response = requests.get(url, headers=headers)
    print_response(response)
    if response.status_code != 401:
        print("❌ Accessing protected route with malformed token should return 401")
        return False
    
    print("✅ Authentication errors correctly return 401 status codes")
    return True

def test_category_partial_update():
    """Test category update endpoint with partial data"""
    print_test_header("Category Partial Update")
    
    if "admin" not in tokens or not test_category_id:
        print("❌ Cannot test category update without admin token or category ID")
        return False
    
    # Test with only description field
    update_data = {
        "description": f"Updated Description {uuid.uuid4().hex[:8]}"
    }
    response = make_request("PUT", f"/api/categories/{test_category_id}", update_data, token=tokens["admin"])
    if response.status_code != 200 or response.json()["description"] != update_data["description"]:
        print("❌ Partial update with only description failed")
        return False
    
    # Test with only color field
    update_data = {
        "color": "#654321"
    }
    response = make_request("PUT", f"/api/categories/{test_category_id}", update_data, token=tokens["admin"])
    if response.status_code != 200 or response.json()["color"] != update_data["color"]:
        print("❌ Partial update with only color failed")
        return False
    
    # Test with only icon field
    update_data = {
        "icon": "new-icon"
    }
    response = make_request("PUT", f"/api/categories/{test_category_id}", update_data, token=tokens["admin"])
    if response.status_code != 200 or response.json()["icon"] != update_data["icon"]:
        print("❌ Partial update with only icon failed")
        return False
    
    print("✅ Category update endpoint correctly accepts partial updates")
    return True

def test_tools_comparison():
    """Test tools comparison functionality with JSON data"""
    print_test_header("Tools Comparison")
    
    if "user" not in tokens or not test_tool_id:
        print("❌ Cannot test tools comparison without user token or tool ID")
        return False
    
    # First, make sure the tool is not in comparison
    response = make_request("DELETE", f"/api/tools/compare/{test_tool_id}", token=tokens["user"], expected_status=[200, 404])
    
    # Test add to comparison with JSON data
    comparison_data = {"tool_id": test_tool_id}
    response = make_request("POST", "/api/tools/compare", comparison_data, token=tokens["user"])
    if response.status_code != 200:
        print("❌ Add to comparison with JSON data failed")
        return False
    
    # Verify the tool was added to comparison
    response = make_request("GET", "/api/tools/compare", token=tokens["user"])
    if response.status_code != 200:
        print("❌ Get comparison tools failed")
        return False
    
    tool_ids = [tool["id"] for tool in response.json()]
    if test_tool_id not in tool_ids:
        print("❌ Tool was not added to comparison")
        return False
    
    # Clean up - remove from comparison
    response = make_request("DELETE", f"/api/tools/compare/{test_tool_id}", token=tokens["user"])
    if response.status_code != 200:
        print("❌ Remove from comparison failed")
        return False
    
    print("✅ Tools comparison functionality works correctly with JSON data")
    return True

def test_protected_routes():
    """Test role-based access control and proper authentication handling"""
    print_test_header("Protected Routes")
    
    if "user" not in tokens or "admin" not in tokens:
        print("❌ Cannot test protected routes without user and admin tokens")
        return False
    
    # Test user accessing admin-only route
    response = make_request("GET", "/api/admin/seo/optimizations", token=tokens["user"], expected_status=403)
    if response.status_code != 403:
        print("❌ User accessing admin-only route should return 403")
        return False
    
    # Test admin accessing admin-only route
    response = make_request("GET", "/api/admin/seo/optimizations", token=tokens["admin"])
    if response.status_code != 200:
        print("❌ Admin accessing admin-only route failed")
        return False
    
    # Test accessing route without authentication
    response = make_request("GET", "/api/auth/me", expected_status=401)
    if response.status_code != 401:
        print("❌ Accessing protected route without authentication should return 401")
        return False
    
    # Test accessing route with authentication
    response = make_request("GET", "/api/auth/me", token=tokens["user"])
    if response.status_code != 200:
        print("❌ Accessing protected route with authentication failed")
        return False
    
    print("✅ Protected routes and role-based access control work correctly")
    return True

def run_tests():
    """Run all tests for fixed issues"""
    print_test_header("TESTING FIXED ISSUES")
    
    # Setup
    if not login_users():
        print("❌ Failed to login users, cannot proceed with tests")
        return
    
    if not create_test_category():
        print("❌ Failed to create test category, cannot proceed with all tests")
    
    if not create_test_tool():
        print("❌ Failed to create test tool, cannot proceed with all tests")
    
    # Run tests for fixed issues
    results = {}
    results["authentication_status_codes"] = test_authentication_status_codes()
    results["category_partial_update"] = test_category_partial_update()
    results["tools_comparison"] = test_tools_comparison()
    results["protected_routes"] = test_protected_routes()
    
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
        print("\n🎉 All fixed issues tests passed!")
    else:
        print("\n⚠️ Some tests failed! The backend still has issues.")

if __name__ == "__main__":
    run_tests()