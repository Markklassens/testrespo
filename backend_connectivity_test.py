#!/usr/bin/env python3
"""
MarketMindAI Backend Comprehensive Testing
Focus: Health Check, CORS, Error Handling, Database Operations, API Endpoints, Request/Response Logging
"""

import requests
import json
import time
import uuid
import os
from typing import Dict, Any, Optional
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

print(f"🔗 Using backend URL: {BACKEND_URL}")

# Admin credentials for authentication testing
ADMIN_CREDENTIALS = {
    "email": "admin@marketmindai.com",
    "password": "admin123"
}

def print_test_header(test_name: str) -> None:
    """Print a formatted test header"""
    print("\n" + "=" * 80)
    print(f"🧪 TEST: {test_name}")
    print("=" * 80)

def print_response_details(response: requests.Response, show_headers: bool = True) -> None:
    """Print detailed response information"""
    print(f"📊 Status Code: {response.status_code}")
    
    if show_headers:
        print("📋 Response Headers:")
        for key, value in response.headers.items():
            print(f"   {key}: {value}")
    
    try:
        response_json = response.json()
        print(f"📄 Response Body: {json.dumps(response_json, indent=2)}")
    except:
        print(f"📄 Response Text: {response.text[:500]}...")

def make_authenticated_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    token: Optional[str] = None,
    expected_status: int = 200,
    params: Optional[Dict[str, Any]] = None,
    show_details: bool = True
) -> requests.Response:
    """Make an HTTP request with detailed logging"""
    url = f"{BACKEND_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    print(f"🚀 {method.upper()} {url}")
    if data:
        print(f"📤 Request Data: {json.dumps(data, indent=2)}")
    
    try:
        if method.lower() == "get":
            response = requests.get(url, headers=headers, params=params, timeout=30)
        elif method.lower() == "post":
            response = requests.post(url, json=data, headers=headers, params=params, timeout=30)
        elif method.lower() == "put":
            response = requests.put(url, json=data, headers=headers, params=params, timeout=30)
        elif method.lower() == "delete":
            response = requests.delete(url, headers=headers, params=params, timeout=30)
        elif method.lower() == "options":
            response = requests.options(url, headers=headers, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        if show_details:
            print_response_details(response)
        
        if response.status_code == expected_status:
            print(f"✅ Expected status code {expected_status}")
        else:
            print(f"❌ Expected status code {expected_status}, got {response.status_code}")
        
        return response
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        raise

def test_health_check_connectivity():
    """Test /api/health endpoint for database connectivity"""
    print_test_header("Health Check & Database Connectivity")
    
    success = True
    
    # Test basic health check
    print("🔍 Testing basic health check...")
    response = make_authenticated_request("GET", "/api/health")
    
    if response.status_code != 200:
        print("❌ Health check endpoint failed")
        success = False
    else:
        health_data = response.json()
        
        # Verify required fields
        required_fields = ["status", "app", "version", "timestamp", "database", "services"]
        for field in required_fields:
            if field not in health_data:
                print(f"❌ Missing required field in health response: {field}")
                success = False
        
        # Check database connectivity status
        if health_data.get("database") == "connected":
            print("✅ Database connectivity confirmed via health check")
        else:
            print(f"❌ Database connectivity issue: {health_data.get('database')}")
            success = False
        
        # Check services status
        services = health_data.get("services", {})
        if services.get("database") == "connected":
            print("✅ Database service status confirmed")
        else:
            print(f"❌ Database service status issue: {services.get('database')}")
            success = False
    
    return success

def test_debug_connectivity():
    """Test /api/debug/connectivity endpoint for comprehensive debug info"""
    print_test_header("Debug Connectivity Endpoint")
    
    success = True
    
    print("🔍 Testing debug connectivity endpoint...")
    response = make_authenticated_request("GET", "/api/debug/connectivity")
    
    if response.status_code != 200:
        print("❌ Debug connectivity endpoint failed")
        success = False
    else:
        debug_data = response.json()
        
        # Verify required debug fields
        required_fields = ["timestamp", "environment", "cors_origins", "database_test"]
        for field in required_fields:
            if field not in debug_data:
                print(f"❌ Missing required field in debug response: {field}")
                success = False
        
        # Check environment variables
        env_data = debug_data.get("environment", {})
        if "DATABASE_URL" in env_data and env_data["DATABASE_URL"]:
            print("✅ Database URL environment variable confirmed")
        else:
            print("❌ Database URL environment variable missing or false")
            success = False
        
        # Check CORS origins
        cors_origins = debug_data.get("cors_origins", [])
        if isinstance(cors_origins, list) and len(cors_origins) > 0:
            print(f"✅ CORS origins configured: {len(cors_origins)} origins")
            print(f"   Sample origins: {cors_origins[:3]}")
        else:
            print("❌ CORS origins not properly configured")
            success = False
        
        # Check database test result
        db_test = debug_data.get("database_test")
        if db_test == "success":
            print("✅ Database test successful")
            
            # Check database info if available
            db_info = debug_data.get("database_info", {})
            if "user_count" in db_info:
                print(f"✅ Database info available - User count: {db_info['user_count']}")
            if "engine_pool_size" in db_info:
                print(f"✅ Connection pool info - Size: {db_info['engine_pool_size']}")
        else:
            print(f"❌ Database test failed: {db_test}")
            success = False
    
    return success

def test_cors_configuration():
    """Test CORS headers and preflight requests"""
    print_test_header("CORS Configuration Testing")
    
    success = True
    
    # Test 1: OPTIONS preflight request
    print("🔍 Testing OPTIONS preflight request...")
    response = make_authenticated_request("OPTIONS", "/api/health", show_details=False)
    
    # Check CORS headers in response
    cors_headers = {
        "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
        "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
        "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
        "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials")
    }
    
    print("📋 CORS Headers Found:")
    critical_headers = ["Access-Control-Allow-Origin", "Access-Control-Allow-Methods", "Access-Control-Allow-Headers"]
    
    for header, value in cors_headers.items():
        if value:
            print(f"   ✅ {header}: {value}")
        else:
            if header in critical_headers:
                print(f"   ❌ {header}: Not present (CRITICAL)")
                success = False
            else:
                print(f"   ⚠️  {header}: Not present (optional)")
    
    # Test 2: Actual request with Origin header
    print("\n🔍 Testing request with Origin header...")
    test_origins = [
        "https://96c19268-7ccd-42f7-9fb8-40015993c1c5.preview.emergentagent.com",
        "http://localhost:3000",
        "https://localhost:3000"
    ]
    
    for origin in test_origins:
        print(f"\n   Testing origin: {origin}")
        headers = {"Origin": origin}
        
        try:
            response = requests.get(f"{BACKEND_URL}/api/health", headers=headers, timeout=30)
            
            # Check if CORS headers are present
            allow_origin = response.headers.get("Access-Control-Allow-Origin")
            if allow_origin:
                if allow_origin == "*" or allow_origin == origin:
                    print(f"   ✅ Origin {origin} allowed")
                else:
                    print(f"   ❌ Origin {origin} not properly handled - got {allow_origin}")
                    success = False
            else:
                print(f"   ❌ No Access-Control-Allow-Origin header for {origin}")
                success = False
                
        except Exception as e:
            print(f"   ❌ Request failed for origin {origin}: {e}")
            success = False
    
    # Test 3: Test specific CORS preflight endpoint
    print("\n🔍 Testing specific CORS preflight endpoint...")
    response = make_authenticated_request("OPTIONS", "/api/test-path", expected_status=200, show_details=False)
    
    if response.status_code == 200:
        print("✅ CORS preflight endpoint working")
    else:
        print(f"❌ CORS preflight endpoint failed with status {response.status_code}")
        success = False
    
    return success

def test_enhanced_error_handling():
    """Test enhanced error handling with proper HTTP status codes"""
    print_test_header("Enhanced Error Handling")
    
    success = True
    
    # Test 1: 404 Not Found
    print("🔍 Testing 404 Not Found...")
    response = make_authenticated_request("GET", f"/api/tools/{uuid.uuid4()}", expected_status=404, show_details=False)
    
    if response.status_code == 404:
        print("✅ 404 error handling working")
        try:
            error_data = response.json()
            if "detail" in error_data:
                print(f"✅ Error message format correct: {error_data['detail']}")
            else:
                print("❌ Error response missing 'detail' field")
                success = False
        except:
            print("❌ Error response not in JSON format")
            success = False
    else:
        print(f"❌ Expected 404, got {response.status_code}")
        success = False
    
    # Test 2: 401 Unauthorized
    print("\n🔍 Testing 401 Unauthorized...")
    response = make_authenticated_request("GET", "/api/auth/me", expected_status=401, show_details=False)
    
    if response.status_code == 401:
        print("✅ 401 error handling working")
        try:
            error_data = response.json()
            if "detail" in error_data:
                print(f"✅ Unauthorized error message: {error_data['detail']}")
            else:
                print("❌ Unauthorized error response missing 'detail' field")
                success = False
        except:
            print("❌ Unauthorized error response not in JSON format")
            success = False
    else:
        print(f"❌ Expected 401, got {response.status_code}")
        success = False
    
    # Test 3: 422 Validation Error
    print("\n🔍 Testing 422 Validation Error...")
    invalid_data = {"invalid": "data"}
    response = make_authenticated_request("POST", "/api/auth/register", data=invalid_data, expected_status=422, show_details=False)
    
    if response.status_code == 422:
        print("✅ 422 validation error handling working")
        try:
            error_data = response.json()
            if "detail" in error_data and isinstance(error_data["detail"], list):
                print(f"✅ Validation error format correct with {len(error_data['detail'])} errors")
            else:
                print("❌ Validation error response format incorrect")
                success = False
        except:
            print("❌ Validation error response not in JSON format")
            success = False
    else:
        print(f"❌ Expected 422, got {response.status_code}")
        success = False
    
    # Test 4: Get admin token for 403 testing
    print("\n🔍 Getting admin token for 403 testing...")
    login_response = make_authenticated_request("POST", "/api/auth/login", data=ADMIN_CREDENTIALS, show_details=False)
    
    if login_response.status_code == 200:
        admin_token = login_response.json()["access_token"]
        print("✅ Admin token obtained")
        
        # Test 403 Forbidden (admin trying to access superadmin endpoint)
        print("\n🔍 Testing 403 Forbidden...")
        response = make_authenticated_request("GET", "/api/superadmin/users", token=admin_token, expected_status=403, show_details=False)
        
        if response.status_code == 403:
            print("✅ 403 forbidden error handling working")
            try:
                error_data = response.json()
                if "detail" in error_data:
                    print(f"✅ Forbidden error message: {error_data['detail']}")
                else:
                    print("❌ Forbidden error response missing 'detail' field")
                    success = False
            except:
                print("❌ Forbidden error response not in JSON format")
                success = False
        else:
            print(f"❌ Expected 403, got {response.status_code}")
            success = False
    else:
        print("❌ Could not obtain admin token for 403 testing")
        success = False
    
    return success

def test_database_operations():
    """Test database operations and connection pooling"""
    print_test_header("Database Operations Testing")
    
    success = True
    
    # Test 1: Basic database connectivity through API
    print("🔍 Testing basic database connectivity...")
    response = make_authenticated_request("GET", "/api/tools/categories", show_details=False)
    
    if response.status_code == 200:
        categories = response.json()
        if isinstance(categories, list):
            print(f"✅ Database read operation successful - {len(categories)} categories found")
        else:
            print("❌ Database read operation returned unexpected format")
            success = False
    else:
        print(f"❌ Database read operation failed with status {response.status_code}")
        success = False
    
    # Test 2: Test database through tools endpoint
    print("\n🔍 Testing database through tools endpoint...")
    response = make_authenticated_request("GET", "/api/tools/search?per_page=5", show_details=False)
    
    if response.status_code == 200:
        tools_data = response.json()
        if isinstance(tools_data, dict) and "tools" in tools_data:
            tools = tools_data["tools"]
            print(f"✅ Database tools query successful - {len(tools)} tools found")
        else:
            print("❌ Database tools query returned unexpected format")
            success = False
    else:
        print(f"❌ Database tools query failed with status {response.status_code}")
        success = False
    
    # Test 3: Test database connection pool status through debug endpoint
    print("\n🔍 Testing database connection pool status...")
    response = make_authenticated_request("GET", "/api/debug/connectivity", show_details=False)
    
    if response.status_code == 200:
        debug_data = response.json()
        db_info = debug_data.get("database_info", {})
        
        if db_info:
            pool_size = db_info.get("engine_pool_size")
            checked_in = db_info.get("engine_pool_checked_in")
            checked_out = db_info.get("engine_pool_checked_out")
            
            print(f"✅ Connection pool info available:")
            print(f"   Pool size: {pool_size}")
            print(f"   Checked in: {checked_in}")
            print(f"   Checked out: {checked_out}")
        else:
            print("❌ Connection pool information not available")
            success = False
    else:
        print(f"❌ Could not retrieve connection pool status")
        success = False
    
    # Test 4: Test table structure verification
    print("\n🔍 Testing table structure through user count...")
    response = make_authenticated_request("GET", "/api/debug/connectivity", show_details=False)
    
    if response.status_code == 200:
        debug_data = response.json()
        db_info = debug_data.get("database_info", {})
        user_count = db_info.get("user_count")
        
        if user_count is not None:
            print(f"✅ Table structure verified - User count: {user_count}")
        else:
            print("❌ Could not verify table structure")
            success = False
    else:
        print("❌ Could not verify database table structure")
        success = False
    
    return success

def test_api_endpoints():
    """Test key API endpoints"""
    print_test_header("API Endpoint Testing")
    
    success = True
    
    # Test 1: Root endpoint (serves frontend HTML)
    print("🔍 Testing root endpoint...")
    response = make_authenticated_request("GET", "/", show_details=False)
    
    if response.status_code == 200:
        # Root endpoint serves HTML frontend, not JSON API
        if "MarketMindAI" in response.text and "<!DOCTYPE html>" in response.text:
            print("✅ Root endpoint working - Serving frontend HTML")
        else:
            print("❌ Root endpoint not serving expected frontend content")
            success = False
    else:
        print(f"❌ Root endpoint failed with status {response.status_code}")
        success = False
    
    # Test 2: Health endpoint (already tested but verify again)
    print("\n🔍 Testing health endpoint...")
    response = make_authenticated_request("GET", "/api/health", show_details=False)
    
    if response.status_code == 200:
        health_data = response.json()
        if health_data.get("status") == "healthy":
            print("✅ Health endpoint working and status healthy")
        else:
            print(f"❌ Health endpoint status not healthy: {health_data.get('status')}")
            success = False
    else:
        print(f"❌ Health endpoint failed with status {response.status_code}")
        success = False
    
    # Test 3: Debug connectivity endpoint (already tested but verify again)
    print("\n🔍 Testing debug connectivity endpoint...")
    response = make_authenticated_request("GET", "/api/debug/connectivity", show_details=False)
    
    if response.status_code == 200:
        debug_data = response.json()
        if "timestamp" in debug_data and "database_test" in debug_data:
            print("✅ Debug connectivity endpoint working")
        else:
            print("❌ Debug connectivity endpoint missing required fields")
            success = False
    else:
        print(f"❌ Debug connectivity endpoint failed with status {response.status_code}")
        success = False
    
    # Test 4: CORS preflight endpoint
    print("\n🔍 Testing CORS preflight endpoint...")
    response = make_authenticated_request("OPTIONS", "/api/test-endpoint", expected_status=200, show_details=False)
    
    if response.status_code == 200:
        print("✅ CORS preflight endpoint working")
    else:
        print(f"❌ CORS preflight endpoint failed with status {response.status_code}")
        success = False
    
    return success

def test_request_response_logging():
    """Test request/response logging and debug headers"""
    print_test_header("Request/Response Logging")
    
    success = True
    
    # Test 1: Check for debug headers
    print("🔍 Testing debug headers in response...")
    response = make_authenticated_request("GET", "/api/health", show_details=False)
    
    # Check for X-Request-ID header
    request_id = response.headers.get("X-Request-ID")
    if request_id:
        print(f"✅ X-Request-ID header present: {request_id}")
    else:
        print("❌ X-Request-ID header missing")
        success = False
    
    # Check for X-Process-Time header
    process_time = response.headers.get("X-Process-Time")
    if process_time:
        try:
            time_float = float(process_time)
            print(f"✅ X-Process-Time header present: {time_float:.4f}s")
        except ValueError:
            print(f"❌ X-Process-Time header invalid format: {process_time}")
            success = False
    else:
        print("❌ X-Process-Time header missing")
        success = False
    
    # Test 2: Test multiple requests to verify logging consistency
    print("\n🔍 Testing logging consistency across multiple requests...")
    request_ids = []
    process_times = []
    
    for i in range(3):
        response = make_authenticated_request("GET", "/api/health", show_details=False)
        
        req_id = response.headers.get("X-Request-ID")
        proc_time = response.headers.get("X-Process-Time")
        
        if req_id:
            request_ids.append(req_id)
        if proc_time:
            try:
                process_times.append(float(proc_time))
            except ValueError:
                pass
    
    # Verify unique request IDs
    if len(set(request_ids)) == len(request_ids) and len(request_ids) == 3:
        print("✅ Request IDs are unique across requests")
    else:
        print("❌ Request IDs are not unique or missing")
        success = False
    
    # Verify process times are reasonable
    if len(process_times) == 3 and all(0 < t < 10 for t in process_times):
        avg_time = sum(process_times) / len(process_times)
        print(f"✅ Process times are reasonable - Average: {avg_time:.4f}s")
    else:
        print("❌ Process times are unreasonable or missing")
        success = False
    
    # Test 3: Test with authentication to verify logging works with auth
    print("\n🔍 Testing logging with authentication...")
    login_response = make_authenticated_request("POST", "/api/auth/login", data=ADMIN_CREDENTIALS, show_details=False)
    
    if login_response.status_code == 200:
        admin_token = login_response.json()["access_token"]
        
        # Make authenticated request
        auth_response = make_authenticated_request("GET", "/api/auth/me", token=admin_token, show_details=False)
        
        # Check debug headers on authenticated request
        auth_req_id = auth_response.headers.get("X-Request-ID")
        auth_proc_time = auth_response.headers.get("X-Process-Time")
        
        if auth_req_id and auth_proc_time:
            print("✅ Debug headers present on authenticated requests")
        else:
            print("❌ Debug headers missing on authenticated requests")
            success = False
    else:
        print("❌ Could not test authenticated request logging")
        success = False
    
    return success

def run_comprehensive_backend_tests():
    """Run all comprehensive backend tests"""
    print("🚀 Starting MarketMindAI Backend Comprehensive Testing")
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Health Check & Connectivity", test_health_check_connectivity),
        ("Debug Connectivity", test_debug_connectivity),
        ("CORS Configuration", test_cors_configuration),
        ("Enhanced Error Handling", test_enhanced_error_handling),
        ("Database Operations", test_database_operations),
        ("API Endpoints", test_api_endpoints),
        ("Request/Response Logging", test_request_response_logging)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            test_results[test_name] = result
            
            if result:
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"\n💥 {test_name}: ERROR - {e}")
            test_results[test_name] = False
    
    # Print final summary
    print("\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\n📈 Overall Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Backend is fully functional.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_comprehensive_backend_tests()
    exit(0 if success else 1)