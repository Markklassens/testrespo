import requests
import json
import time
import uuid
import random
import string
import os
import io
import csv
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()

# Get backend URL from environment
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "http://localhost:8001")

# Test data
SUPER_ADMIN_USER = {
    "email": "superadmin@marketmindai.com",
    "password": "superadmin123"
}

# Store tokens
tokens = {}
test_tool_id = None
test_category_id = None

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

def test_super_admin_login():
    """Test super admin login"""
    print_test_header("Super Admin Login")
    
    login_data = {
        "email": SUPER_ADMIN_USER["email"],
        "password": SUPER_ADMIN_USER["password"]
    }
    
    response = make_request("POST", "/api/auth/login", login_data)
    if response.status_code != 200:
        print("❌ Super admin login failed")
        return False
    
    # Store token for later use
    tokens["superadmin"] = response.json()["access_token"]
    print("✅ Super admin login passed")
    return True

def test_tools_crud_with_super_admin():
    """Test tools CRUD operations with super admin permissions"""
    print_test_header("Tools CRUD with Super Admin")
    
    if "superadmin" not in tokens:
        print("❌ Cannot test tools CRUD without super admin token")
        return False
    
    global test_tool_id, test_category_id
    
    # First, get or create a category for the tool
    response = make_request("GET", "/api/categories", token=tokens["superadmin"])
    if response.status_code != 200:
        print("❌ Failed to get categories")
        return False
    
    categories = response.json()
    if categories:
        test_category_id = categories[0]["id"]
        print(f"Using existing category with ID: {test_category_id}")
    else:
        # Create a category
        category_data = {
            "name": f"Test Category {uuid.uuid4().hex[:8]}",
            "description": "Test Category Description",
            "icon": "test-icon",
            "color": "#123456"
        }
        response = make_request("POST", "/api/categories", category_data, token=tokens["superadmin"])
        if response.status_code != 200:
            print("❌ Failed to create category")
            return False
        
        test_category_id = response.json()["id"]
        print(f"Created new category with ID: {test_category_id}")
    
    # Test CREATE tool
    tool_data = {
        "name": f"Test Super Admin Tool {uuid.uuid4().hex[:8]}",
        "description": "This is a test tool created by super admin",
        "short_description": "Super admin test tool",
        "category_id": test_category_id,
        "pricing_model": "Freemium",
        "company_size": "Enterprise",
        "slug": f"test-super-admin-tool-{uuid.uuid4().hex[:8]}",
        "is_hot": True,
        "is_featured": True,
        "industry": "Technology",
        "employee_size": "201-1000",
        "revenue_range": "10M-100M",
        "location": "San Francisco, CA"
    }
    
    response = make_request("POST", "/api/tools", tool_data, token=tokens["superadmin"])
    if response.status_code != 200:
        print("❌ CREATE tool failed")
        return False
    
    test_tool_id = response.json()["id"]
    print(f"✅ Created tool with ID: {test_tool_id}")
    
    # Test GET tool by ID
    response = make_request("GET", f"/api/tools/{test_tool_id}", token=tokens["superadmin"])
    if response.status_code != 200 or response.json()["id"] != test_tool_id:
        print("❌ GET tool by ID failed")
        return False
    
    print("✅ GET tool by ID passed")
    
    # Test UPDATE tool
    update_data = {
        "description": f"Updated description by super admin {uuid.uuid4().hex[:8]}",
        "is_featured": True,
        "meta_title": "Super Admin Test Tool",
        "meta_description": "This is a test tool updated by super admin"
    }
    
    response = make_request("PUT", f"/api/tools/{test_tool_id}", update_data, token=tokens["superadmin"])
    if response.status_code != 200 or response.json()["description"] != update_data["description"]:
        print("❌ UPDATE tool failed")
        return False
    
    print("✅ UPDATE tool passed")
    
    # Test DELETE tool (we'll create a temporary tool for this)
    temp_tool_data = {
        "name": f"Temp Tool to Delete {uuid.uuid4().hex[:8]}",
        "description": "This tool will be deleted",
        "short_description": "Temp tool",
        "category_id": test_category_id,
        "slug": f"temp-tool-{uuid.uuid4().hex[:8]}"
    }
    
    response = make_request("POST", "/api/tools", temp_tool_data, token=tokens["superadmin"])
    if response.status_code != 200:
        print("❌ Failed to create temporary tool for deletion test")
        return False
    
    temp_tool_id = response.json()["id"]
    
    response = make_request("DELETE", f"/api/tools/{temp_tool_id}", token=tokens["superadmin"])
    if response.status_code != 200:
        print("❌ DELETE tool failed")
        return False
    
    print("✅ DELETE tool passed")
    
    # Verify the tool was deleted
    response = make_request("GET", f"/api/tools/{temp_tool_id}", expected_status=404)
    if response.status_code != 404:
        print("❌ Tool deletion verification failed")
        return False
    
    print("✅ Tool deletion verification passed")
    print("✅ Tools CRUD with Super Admin passed")
    return True

def test_csv_template_download():
    """Test CSV template download"""
    print_test_header("CSV Template Download")
    
    if "superadmin" not in tokens:
        print("❌ Cannot test CSV template download without super admin token")
        return False
    
    response = make_request("GET", "/api/admin/tools/sample-csv", token=tokens["superadmin"])
    if response.status_code != 200:
        print("❌ CSV template download failed")
        return False
    
    # Check if the response is a CSV file
    content_type = response.headers.get("Content-Type")
    if not content_type or "text/csv" not in content_type:
        print(f"❌ Expected content type 'text/csv', got '{content_type}'")
        return False
    
    # Check if the response has the Content-Disposition header
    content_disposition = response.headers.get("Content-Disposition")
    if not content_disposition or "attachment" not in content_disposition:
        print(f"❌ Expected Content-Disposition header with 'attachment', got '{content_disposition}'")
        return False
    
    # Try to parse the CSV content
    try:
        csv_content = response.text
        csv_reader = csv.reader(io.StringIO(csv_content))
        headers = next(csv_reader)
        
        # Check if the CSV has the expected headers
        expected_headers = ["name", "description", "category_id"]
        for header in expected_headers:
            if header not in headers:
                print(f"❌ Missing expected header in CSV template: {header}")
                return False
        
        print(f"✅ CSV template has expected headers: {headers}")
        
        # Check if there's at least one sample row
        sample_row = next(csv_reader, None)
        if not sample_row:
            print("❌ CSV template doesn't contain a sample row")
            return False
        
        print(f"✅ CSV template contains a sample row: {sample_row}")
        
    except Exception as e:
        print(f"❌ Failed to parse CSV content: {str(e)}")
        return False
    
    print("✅ CSV template download passed")
    return True

def test_bulk_upload_functionality():
    """Test bulk upload functionality"""
    print_test_header("Bulk Upload Functionality")
    
    if "superadmin" not in tokens or not test_category_id:
        print("❌ Cannot test bulk upload without super admin token or category ID")
        return False
    
    # Create a CSV file for bulk upload
    csv_data = io.StringIO()
    csv_writer = csv.writer(csv_data)
    
    # Write headers
    csv_writer.writerow([
        "name", "description", "short_description", "category_id", 
        "pricing_model", "company_size", "slug", "is_hot", "is_featured",
        "industry", "employee_size", "revenue_range", "location"
    ])
    
    # Write 3 sample tools
    for i in range(3):
        tool_name = f"Bulk Upload Tool {i+1} {uuid.uuid4().hex[:6]}"
        csv_writer.writerow([
            tool_name,
            f"Description for {tool_name}",
            f"Short description for {tool_name}",
            test_category_id,
            "Freemium",
            "SMB",
            tool_name.lower().replace(" ", "-"),
            "true" if i % 2 == 0 else "false",
            "true" if i % 3 == 0 else "false",
            "Technology",
            "11-50",
            "1M-10M",
            "New York, NY"
        ])
    
    # Reset the cursor to the beginning of the StringIO object
    csv_data.seek(0)
    
    # Create a file-like object for the request
    files = {
        "file": ("bulk_upload_test.csv", csv_data.getvalue(), "text/csv")
    }
    
    # Make the request
    response = make_request(
        "POST", 
        "/api/tools/bulk-upload", 
        token=tokens["superadmin"],
        files=files
    )
    
    if response.status_code != 200:
        print("❌ Bulk upload failed")
        return False
    
    # Check the response
    result = response.json()
    if "created_count" not in result or result["created_count"] != 3:
        print(f"❌ Expected to create 3 tools, but got {result.get('created_count', 0)}")
        return False
    
    if "errors" in result and result["errors"]:
        print(f"❌ Bulk upload had errors: {result['errors']}")
        return False
    
    print(f"✅ Successfully created {result['created_count']} tools via bulk upload")
    print("✅ Bulk upload functionality passed")
    return True

def test_discover_page_integration():
    """Test that created tools appear in search results and analytics"""
    print_test_header("Discover Page Integration")
    
    if not test_tool_id:
        print("❌ Cannot test discover page integration without a test tool ID")
        return False
    
    # Test search endpoint
    response = make_request("GET", "/api/tools/search")
    if response.status_code != 200:
        print("❌ Tools search endpoint failed")
        return False
    
    # Check if our test tool appears in the search results
    search_results = response.json()
    tool_found = False
    
    for tool in search_results["tools"]:
        if tool["id"] == test_tool_id:
            tool_found = True
            break
    
    if not tool_found:
        print("❌ Test tool not found in search results")
        # Try searching with the specific tool ID
        response = make_request("GET", f"/api/tools/search?q={test_tool_id}")
        if response.status_code != 200:
            print("❌ Targeted search failed")
            return False
        
        # Check again
        search_results = response.json()
        for tool in search_results["tools"]:
            if tool["id"] == test_tool_id:
                tool_found = True
                print("✅ Test tool found in targeted search results")
                break
        
        if not tool_found:
            print("❌ Test tool not found even in targeted search")
            return False
    else:
        print("✅ Test tool found in search results")
    
    # Test analytics endpoint
    response = make_request("GET", "/api/tools/analytics")
    if response.status_code != 200:
        print("❌ Tools analytics endpoint failed")
        return False
    
    # Check if our test tool appears in any of the analytics sections
    analytics = response.json()
    tool_found = False
    
    for section in ["trending_tools", "top_rated_tools", "most_viewed_tools", "newest_tools", "featured_tools", "hot_tools"]:
        for tool in analytics[section]:
            if tool["id"] == test_tool_id:
                tool_found = True
                print(f"✅ Test tool found in {section}")
                break
        if tool_found:
            break
    
    if not tool_found:
        print("⚠️ Test tool not found in any analytics section. This might be expected if the tool is new or not featured/hot.")
    
    # Test category analytics
    response = make_request("GET", "/api/categories/analytics")
    if response.status_code != 200:
        print("❌ Categories analytics endpoint failed")
        return False
    
    # Check if our test tool appears in the recommended tools for its category
    category_analytics = response.json()
    tool_found = False
    
    for category in category_analytics:
        if category["category_id"] == test_category_id:
            for tool in category["recommended_tools"]:
                if tool["id"] == test_tool_id:
                    tool_found = True
                    print(f"✅ Test tool found in recommended tools for its category")
                    break
            break
    
    if not tool_found:
        print("⚠️ Test tool not found in recommended tools for its category. This might be expected if the tool is new or has a low rating.")
    
    print("✅ Discover page integration passed")
    return True

def run_super_admin_tests():
    """Run all super admin tests"""
    results = {}
    
    try:
        # Super Admin Authentication
        results["super_admin_login"] = test_super_admin_login()
        
        # Tools CRUD Operations with super admin permissions
        if results["super_admin_login"]:
            results["tools_crud_with_super_admin"] = test_tools_crud_with_super_admin()
        else:
            results["tools_crud_with_super_admin"] = False
            print("❌ Skipping tools CRUD test due to login failure")
        
        # CSV Template Download
        if "superadmin" in tokens:
            results["csv_template_download"] = test_csv_template_download()
        else:
            results["csv_template_download"] = False
            print("❌ Skipping CSV template download test due to login failure")
        
        # Bulk Upload Functionality
        if "superadmin" in tokens and test_category_id:
            results["bulk_upload_functionality"] = test_bulk_upload_functionality()
        else:
            results["bulk_upload_functionality"] = False
            print("❌ Skipping bulk upload test due to login failure or missing category")
        
        # Discover Page Integration
        if test_tool_id:
            results["discover_page_integration"] = test_discover_page_integration()
        else:
            results["discover_page_integration"] = False
            print("❌ Skipping discover page integration test due to missing test tool")
        
        # Print summary
        print("\n" + "=" * 80)
        print("SUPER ADMIN TESTS SUMMARY")
        print("=" * 80)
        
        all_passed = True
        for test_name, passed in results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_name}: {status}")
            if not passed:
                all_passed = False
        
        if all_passed:
            print("\n🎉 All super admin tests passed!")
        else:
            print("\n⚠️ Some super admin tests failed!")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_super_admin_tests()