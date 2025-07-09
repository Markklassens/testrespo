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

# Get backend URL from environment
BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "http://localhost:8001")

# Seeded users for testing
SEEDED_USERS = [
    {"email": "user@marketmindai.com", "password": "password123", "type": "user"},
    {"email": "admin@marketmindai.com", "password": "admin123", "type": "admin"},
    {"email": "superadmin@marketmindai.com", "password": "superadmin123", "type": "superadmin"}
]

# Store tokens
tokens = {}

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

def login():
    """Login with seeded users to get tokens"""
    print_test_header("Login to get tokens")
    
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
    
    return len(tokens) > 0

def test_categories_endpoint():
    """Test the categories endpoint for DiscoverPage"""
    print_test_header("Categories API Endpoint")
    
    # Test GET categories
    response = make_request("GET", "/api/categories")
    if response.status_code != 200 or not isinstance(response.json(), list):
        print("❌ GET categories failed")
        return False
    
    categories = response.json()
    print(f"Found {len(categories)} categories")
    
    # Verify category structure
    if categories:
        category = categories[0]
        required_fields = ["id", "name", "description", "icon", "color", "created_at"]
        for field in required_fields:
            if field not in category:
                print(f"❌ Missing field in category response: {field}")
                return False
    
    print("✅ Categories API endpoint passed")
    return True

def test_tools_search_endpoint():
    """Test the tools search endpoint for DiscoverPage with various filters and pagination"""
    print_test_header("Tools Search API Endpoint")
    
    # Test basic search without parameters
    print_test_header("Basic search without parameters")
    response = make_request("GET", "/api/tools/search")
    if response.status_code != 200:
        print("❌ Basic search failed")
        return False
    
    # Get total tools count for verification
    total_tools = response.json()["total"]
    print(f"Total tools in database: {total_tools}")
    
    # Test pagination
    print_test_header("Pagination with different page sizes")
    page_sizes = [5, 10, 20, 50]
    for size in page_sizes:
        response = make_request("GET", f"/api/tools/search?page=1&per_page={size}")
        if response.status_code != 200:
            print(f"❌ Pagination with page size {size} failed")
            return False
        
        # Verify correct number of tools returned
        tools = response.json()["tools"]
        expected_count = min(size, total_tools)
        if len(tools) != expected_count:
            print(f"❌ Expected {expected_count} tools, got {len(tools)}")
            return False
        
        print(f"✅ Pagination with page size {size} passed")
    
    # Test search with query parameter
    print_test_header("Search with query parameter")
    search_terms = ["tool", "ai", "marketing"]
    for term in search_terms:
        response = make_request("GET", f"/api/tools/search?q={term}")
        if response.status_code != 200:
            print(f"❌ Search with query '{term}' failed")
            return False
        print(f"✅ Search with query '{term}' passed")
    
    # Test category filtering
    print_test_header("Category filtering")
    # Get a category ID first
    categories_response = make_request("GET", "/api/categories")
    if categories_response.status_code == 200 and categories_response.json():
        category_id = categories_response.json()[0]["id"]
        response = make_request("GET", f"/api/tools/search?category_id={category_id}")
        if response.status_code != 200:
            print("❌ Category filtering failed")
            return False
        print("✅ Category filtering passed")
    
    # Test pricing model filtering
    print_test_header("Pricing model filtering")
    pricing_models = ["Free", "Freemium", "Paid"]
    for model in pricing_models:
        response = make_request("GET", f"/api/tools/search?pricing_model={model}")
        if response.status_code != 200:
            print(f"❌ Pricing model filtering with '{model}' failed")
            return False
        print(f"✅ Pricing model filtering with '{model}' passed")
    
    # Test company size filtering
    print_test_header("Company size filtering")
    company_sizes = ["Startup", "SMB", "Enterprise"]
    for size in company_sizes:
        response = make_request("GET", f"/api/tools/search?company_size={size}")
        if response.status_code != 200:
            print(f"❌ Company size filtering with '{size}' failed")
            return False
        print(f"✅ Company size filtering with '{size}' passed")
    
    # Test industry filtering
    print_test_header("Industry filtering")
    industries = ["Technology", "Finance", "Healthcare", "Marketing"]
    for industry in industries:
        response = make_request("GET", f"/api/tools/search?industry={industry}")
        if response.status_code != 200:
            print(f"❌ Industry filtering with '{industry}' failed")
            return False
        print(f"✅ Industry filtering with '{industry}' passed")
    
    # Test employee size filtering
    print_test_header("Employee size filtering")
    employee_sizes = ["1-10", "11-50", "51-200", "201-1000", "1000+"]
    for size in employee_sizes:
        response = make_request("GET", f"/api/tools/search?employee_size={size}")
        if response.status_code != 200:
            print(f"❌ Employee size filtering with '{size}' failed")
            return False
        print(f"✅ Employee size filtering with '{size}' passed")
    
    # Test revenue range filtering
    print_test_header("Revenue range filtering")
    revenue_ranges = ["<1M", "1M-10M", "10M-100M", "100M+"]
    for range_val in revenue_ranges:
        response = make_request("GET", f"/api/tools/search?revenue_range={range_val}")
        if response.status_code != 200:
            print(f"❌ Revenue range filtering with '{range_val}' failed")
            return False
        print(f"✅ Revenue range filtering with '{range_val}' passed")
    
    # Test location filtering
    print_test_header("Location filtering")
    locations = ["San Francisco", "New York", "London", "Berlin"]
    for location in locations:
        response = make_request("GET", f"/api/tools/search?location={location}")
        if response.status_code != 200:
            print(f"❌ Location filtering with '{location}' failed")
            return False
        print(f"✅ Location filtering with '{location}' passed")
    
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
    
    # Test minimum rating filtering
    print_test_header("Minimum rating filtering")
    ratings = [3.0, 4.0, 4.5]
    for rating in ratings:
        response = make_request("GET", f"/api/tools/search?min_rating={rating}")
        if response.status_code != 200:
            print(f"❌ Minimum rating filtering with '{rating}' failed")
            return False
        print(f"✅ Minimum rating filtering with '{rating}' passed")
    
    # Test sorting options
    print_test_header("Sorting options")
    sort_options = ["rating", "trending", "views", "newest", "oldest", "name"]
    for sort_by in sort_options:
        response = make_request("GET", f"/api/tools/search?sort_by={sort_by}")
        if response.status_code != 200:
            print(f"❌ Sorting by '{sort_by}' failed")
            return False
        print(f"✅ Sorting by '{sort_by}' passed")
    
    # Test combination of filters
    print_test_header("Combination of filters")
    complex_query = "/api/tools/search?pricing_model=Freemium&company_size=SMB&sort_by=rating&is_featured=true&page=1&per_page=20"
    response = make_request("GET", complex_query)
    if response.status_code != 200:
        print("❌ Combination of filters failed")
        return False
    print("✅ Combination of filters passed")
    
    # Test pagination metadata
    print_test_header("Pagination metadata")
    response = make_request("GET", "/api/tools/search?page=1&per_page=10")
    if response.status_code != 200:
        print("❌ Pagination metadata check failed")
        return False
    
    data = response.json()
    expected_pagination_keys = ["total", "page", "per_page", "total_pages", "has_next", "has_prev"]
    for key in expected_pagination_keys:
        if key not in data:
            print(f"❌ Missing pagination key: {key}")
            return False
    
    print("✅ Pagination metadata check passed")
    
    # Test performance with large page size
    print_test_header("Performance with large page size")
    start_time = time.time()
    response = make_request("GET", "/api/tools/search?page=1&per_page=100")
    end_time = time.time()
    
    if response.status_code != 200:
        print("❌ Performance test failed")
        return False
    
    response_time = end_time - start_time
    print(f"Response time: {response_time:.2f} seconds")
    
    # Check if response time is acceptable (under 2 seconds)
    if response_time > 2:
        print(f"⚠️ Response time ({response_time:.2f}s) is higher than expected (2s)")
    else:
        print(f"✅ Response time ({response_time:.2f}s) is acceptable")
    
    print("✅ Tools search API endpoint passed all tests")
    return True

def test_tools_analytics_endpoint():
    """Test the tools analytics endpoint for DiscoverPage carousels"""
    print_test_header("Tools Analytics API Endpoint")
    
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
    
    # Test performance
    print_test_header("Tools Analytics Performance")
    start_time = time.time()
    response = make_request("GET", "/api/tools/analytics")
    end_time = time.time()
    
    if response.status_code != 200:
        print("❌ Performance test failed")
        return False
    
    response_time = end_time - start_time
    print(f"Response time: {response_time:.2f} seconds")
    
    # Check if response time is acceptable (under 2 seconds)
    if response_time > 2:
        print(f"⚠️ Response time ({response_time:.2f}s) is higher than expected (2s)")
    else:
        print(f"✅ Response time ({response_time:.2f}s) is acceptable")
    
    print("✅ Tools analytics endpoint passed - all required carousels present")
    return True

def test_csv_sample_file():
    """Test the CSV sample file download endpoint"""
    print_test_header("CSV Sample File Download")
    
    if "admin" not in tokens:
        print("❌ Cannot test CSV sample file download without admin token")
        return False
    
    # Test GET sample CSV file
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

def test_categories_analytics_endpoint():
    """Test the categories analytics endpoint"""
    print_test_header("Categories Analytics API Endpoint")
    
    response = make_request("GET", "/api/categories/analytics")
    if response.status_code != 200:
        print("❌ Categories analytics endpoint failed")
        return False
    
    data = response.json()
    if not isinstance(data, list):
        print(f"❌ Expected list response, got {type(data)}")
        return False
    
    # Check category analytics structure
    if data:
        category_analytics = data[0]
        required_fields = ["category_id", "category_name", "tool_count", "avg_rating", "total_views", "recommended_tools"]
        for field in required_fields:
            if field not in category_analytics:
                print(f"❌ Missing field in category analytics: {field}")
                return False
        
        # Check recommended tools structure
        if category_analytics["recommended_tools"]:
            tool = category_analytics["recommended_tools"][0]
            required_tool_fields = ["id", "name", "description"]
            for field in required_tool_fields:
                if field not in tool:
                    print(f"❌ Missing field in recommended tool: {field}")
                    return False
    
    print("✅ Categories analytics endpoint passed")
    return True

def run_discover_page_tests():
    """Run all tests for the DiscoverPage API endpoints"""
    print_test_header("DISCOVER PAGE API TESTS")
    
    # Login first to get tokens
    if not login():
        print("❌ Failed to login, cannot proceed with tests requiring authentication")
    
    results = {}
    
    # Test categories endpoint
    results["categories_endpoint"] = test_categories_endpoint()
    
    # Test tools search endpoint
    results["tools_search_endpoint"] = test_tools_search_endpoint()
    
    # Test tools analytics endpoint
    results["tools_analytics_endpoint"] = test_tools_analytics_endpoint()
    
    # Test categories analytics endpoint
    results["categories_analytics_endpoint"] = test_categories_analytics_endpoint()
    
    # Test CSV sample file download endpoint
    results["csv_sample_file"] = test_csv_sample_file()
    
    # Print summary
    print("\n" + "=" * 80)
    print("DISCOVER PAGE API TEST SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All DiscoverPage API tests passed!")
    else:
        print("\n⚠️ Some DiscoverPage API tests failed!")

if __name__ == "__main__":
    run_discover_page_tests()