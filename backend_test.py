#!/usr/bin/env python3
"""
MarketMindAI Backend Testing Suite
Comprehensive testing of backend APIs after database connectivity fixes
"""

import requests
import json
import base64
import os
import time
from datetime import datetime

# Test configuration
BACKEND_URL = "https://f02388c6-521c-4c08-a2f9-869f56db4d75.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials as specified in review request
TEST_USERS = {
    "user": {
        "email": "user@marketmindai.com",
        "password": "password123"
    },
    "admin": {
        "email": "admin@marketmindai.com", 
        "password": "admin123"
    },
    "superadmin": {
        "email": "superadmin@marketmindai.com",
        "password": "superadmin123"
    }
}

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.tokens = {}
        self.test_results = []
        
    def log_test(self, test_name, status, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy" and data.get("database") == "connected":
                    self.log_test("Health Check", "PASS", "Backend and database are healthy", 
                                data.get("services"))
                else:
                    self.log_test("Health Check", "FAIL", f"Unhealthy status: {data.get('status')}, DB: {data.get('database')}")
            else:
                self.log_test("Health Check", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Health Check", "FAIL", f"Connection error: {str(e)}")
    
    def test_authentication(self):
        """Test authentication with all three user types"""
        for user_type, credentials in TEST_USERS.items():
            try:
                # Test login
                login_data = {
                    "email": credentials["email"],
                    "password": credentials["password"]
                }
                
                response = self.session.post(
                    f"{API_BASE}/auth/login",
                    json=login_data,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "access_token" in data:
                        self.tokens[user_type] = data["access_token"]
                        self.log_test(f"Authentication - {user_type.title()}", "PASS", 
                                    f"Login successful, token received")
                        
                        # Test token validation by getting current user
                        headers = {"Authorization": f"Bearer {data['access_token']}"}
                        me_response = self.session.get(f"{API_BASE}/auth/me", headers=headers, timeout=10)
                        
                        if me_response.status_code == 200:
                            user_data = me_response.json()
                            actual_type = user_data.get("user_type")
                            if actual_type == user_type:
                                self.log_test(f"Token Validation - {user_type.title()}", "PASS",
                                            f"Token valid, user type confirmed: {actual_type}")
                            else:
                                self.log_test(f"Token Validation - {user_type.title()}", "FAIL",
                                            f"User type mismatch: expected {user_type}, got {actual_type}")
                        else:
                            self.log_test(f"Token Validation - {user_type.title()}", "FAIL",
                                        f"Token validation failed: HTTP {me_response.status_code}")
                    else:
                        self.log_test(f"Authentication - {user_type.title()}", "FAIL", 
                                    "No access token in response")
                else:
                    self.log_test(f"Authentication - {user_type.title()}", "FAIL", 
                                f"Login failed: HTTP {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test(f"Authentication - {user_type.title()}", "FAIL", f"Error: {str(e)}")
    
    def test_protected_routes(self):
        """Test protected routes access with different user types"""
        if not self.tokens.get("admin"):
            self.log_test("Protected Routes", "SKIP", "No admin token available")
            return
            
        admin_headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Test accessing user profile (should work for authenticated users)
        try:
            response = self.session.get(f"{API_BASE}/auth/me", headers=admin_headers, timeout=10)
            if response.status_code == 200:
                self.log_test("Protected Route - User Profile", "PASS", "Admin can access user profile")
            else:
                self.log_test("Protected Route - User Profile", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Protected Route - User Profile", "FAIL", f"Error: {str(e)}")
        
        # Test accessing without token (should fail with 401)
        try:
            response = self.session.get(f"{API_BASE}/auth/me", timeout=10)
            if response.status_code == 401:
                self.log_test("Protected Route - No Token", "PASS", "Correctly rejected unauthenticated request")
            else:
                self.log_test("Protected Route - No Token", "FAIL", 
                            f"Expected 401, got HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Protected Route - No Token", "FAIL", f"Error: {str(e)}")
    
    def test_blog_crud_operations(self):
        """Test blog CRUD operations"""
        if not self.tokens.get("admin"):
            self.log_test("Blog CRUD", "SKIP", "No admin token available")
            return
            
        admin_headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Test blog listing
        try:
            response = self.session.get(f"{API_BASE}/blogs", timeout=10)
            if response.status_code == 200:
                blogs = response.json()
                self.log_test("Blog Listing", "PASS", f"Retrieved {len(blogs)} blogs")
            else:
                self.log_test("Blog Listing", "FAIL", f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Blog Listing", "FAIL", f"Error: {str(e)}")
        
        # Test blog creation
        try:
            # First get categories to use a valid category_id
            cat_response = self.session.get(f"{API_BASE}/categories", timeout=10)
            if cat_response.status_code == 200:
                categories = cat_response.json()
                if categories:
                    category_id = categories[0]["id"]
                    
                    blog_data = {
                        "title": f"Test Blog {int(time.time())}",
                        "content": "This is a test blog post created during backend testing. It contains sample content to verify the blog creation functionality is working correctly.",
                        "category_id": category_id,
                        "status": "published",
                        "meta_description": "Test blog for backend testing"
                    }
                    
                    response = self.session.post(
                        f"{API_BASE}/blogs",
                        json=blog_data,
                        headers=admin_headers,
                        timeout=10
                    )
                    
                    if response.status_code == 201:
                        blog = response.json()
                        blog_id = blog.get("id")
                        self.log_test("Blog Creation", "PASS", 
                                    f"Blog created successfully with ID: {blog_id}")
                        
                        # Test blog retrieval
                        if blog_id:
                            get_response = self.session.get(f"{API_BASE}/blogs/{blog_id}", timeout=10)
                            if get_response.status_code == 200:
                                retrieved_blog = get_response.json()
                                if retrieved_blog.get("title") == blog_data["title"]:
                                    self.log_test("Blog Retrieval", "PASS", "Blog retrieved successfully")
                                else:
                                    self.log_test("Blog Retrieval", "FAIL", "Retrieved blog data mismatch")
                            else:
                                self.log_test("Blog Retrieval", "FAIL", 
                                            f"HTTP {get_response.status_code}: {get_response.text}")
                    else:
                        self.log_test("Blog Creation", "FAIL", 
                                    f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("Blog Creation", "SKIP", "No categories available for testing")
            else:
                self.log_test("Blog Creation", "SKIP", "Could not retrieve categories")
                
        except Exception as e:
            self.log_test("Blog Creation", "FAIL", f"Error: {str(e)}")
    
    def test_tool_comparison_system(self):
        """Test tool comparison functionality"""
        if not self.tokens.get("admin"):
            self.log_test("Tool Comparison", "SKIP", "No admin token available")
            return
            
        admin_headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Test getting comparison list (should be empty initially)
        try:
            response = self.session.get(f"{API_BASE}/tools/compare", headers=admin_headers, timeout=10)
            if response.status_code == 200:
                comparison_list = response.json()
                self.log_test("Tool Comparison - Get List", "PASS", 
                            f"Retrieved comparison list with {len(comparison_list)} tools")
                
                # Test adding a tool to comparison
                # First get available tools
                tools_response = self.session.get(f"{API_BASE}/tools", timeout=10)
                if tools_response.status_code == 200:
                    tools = tools_response.json()
                    if tools:
                        tool_id = tools[0]["id"]
                        
                        # Add tool to comparison
                        add_response = self.session.post(
                            f"{API_BASE}/tools/compare",
                            json={"tool_id": tool_id},
                            headers=admin_headers,
                            timeout=10
                        )
                        
                        if add_response.status_code == 200:
                            self.log_test("Tool Comparison - Add Tool", "PASS", 
                                        f"Tool {tool_id} added to comparison")
                            
                            # Verify tool was added
                            verify_response = self.session.get(f"{API_BASE}/tools/compare", 
                                                             headers=admin_headers, timeout=10)
                            if verify_response.status_code == 200:
                                updated_list = verify_response.json()
                                if len(updated_list) > len(comparison_list):
                                    self.log_test("Tool Comparison - Verify Add", "PASS", 
                                                "Tool successfully added to comparison list")
                                    
                                    # Test removing tool from comparison
                                    remove_response = self.session.delete(
                                        f"{API_BASE}/tools/compare/{tool_id}",
                                        headers=admin_headers,
                                        timeout=10
                                    )
                                    
                                    if remove_response.status_code == 200:
                                        self.log_test("Tool Comparison - Remove Tool", "PASS", 
                                                    "Tool successfully removed from comparison")
                                    else:
                                        self.log_test("Tool Comparison - Remove Tool", "FAIL", 
                                                    f"HTTP {remove_response.status_code}: {remove_response.text}")
                                else:
                                    self.log_test("Tool Comparison - Verify Add", "FAIL", 
                                                "Tool was not added to comparison list")
                            else:
                                self.log_test("Tool Comparison - Verify Add", "FAIL", 
                                            f"HTTP {verify_response.status_code}: {verify_response.text}")
                        else:
                            self.log_test("Tool Comparison - Add Tool", "FAIL", 
                                        f"HTTP {add_response.status_code}: {add_response.text}")
                    else:
                        self.log_test("Tool Comparison - Add Tool", "SKIP", "No tools available for testing")
                else:
                    self.log_test("Tool Comparison - Add Tool", "SKIP", "Could not retrieve tools")
            else:
                self.log_test("Tool Comparison - Get List", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Tool Comparison", "FAIL", f"Error: {str(e)}")
    
    def test_file_upload_system(self):
        """Test file upload functionality"""
        if not self.tokens.get("admin"):
            self.log_test("File Upload", "SKIP", "No admin token available")
            return
            
        admin_headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Create a small test image (1x1 pixel PNG)
        test_image_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77zgAAAABJRU5ErkJggg=="
        )
        
        try:
            # Test image upload
            files = {"file": ("test.png", test_image_data, "image/png")}
            
            response = self.session.post(
                f"{API_BASE}/user/upload",
                files=files,
                headers={"Authorization": f"Bearer {self.tokens['admin']}"},
                timeout=10
            )
            
            if response.status_code == 200:
                upload_result = response.json()
                if "data_url" in upload_result:
                    self.log_test("File Upload - Image", "PASS", 
                                "Image uploaded successfully, data URL generated")
                else:
                    self.log_test("File Upload - Image", "FAIL", 
                                "No data URL in upload response")
            else:
                self.log_test("File Upload - Image", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("File Upload - Image", "FAIL", f"Error: {str(e)}")
        
        # Test upload without authentication (should fail)
        try:
            files = {"file": ("test.png", test_image_data, "image/png")}
            response = self.session.post(f"{API_BASE}/user/upload", files=files, timeout=10)
            
            if response.status_code == 401:
                self.log_test("File Upload - No Auth", "PASS", 
                            "Upload correctly rejected without authentication")
            else:
                self.log_test("File Upload - No Auth", "FAIL", 
                            f"Expected 401, got HTTP {response.status_code}")
        except Exception as e:
            self.log_test("File Upload - No Auth", "FAIL", f"Error: {str(e)}")
    
    def test_core_api_endpoints(self):
        """Test core API endpoints"""
        # Test categories endpoint
        try:
            response = self.session.get(f"{API_BASE}/categories", timeout=10)
            if response.status_code == 200:
                categories = response.json()
                self.log_test("Core API - Categories", "PASS", 
                            f"Retrieved {len(categories)} categories")
            else:
                self.log_test("Core API - Categories", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Core API - Categories", "FAIL", f"Error: {str(e)}")
        
        # Test tools search with pagination
        try:
            response = self.session.get(f"{API_BASE}/tools/search?page=1&limit=10", timeout=10)
            if response.status_code == 200:
                search_result = response.json()
                if "tools" in search_result and "total" in search_result:
                    self.log_test("Core API - Tools Search", "PASS", 
                                f"Search returned {len(search_result['tools'])} tools out of {search_result['total']}")
                else:
                    self.log_test("Core API - Tools Search", "FAIL", 
                                "Invalid search response structure")
            else:
                self.log_test("Core API - Tools Search", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Core API - Tools Search", "FAIL", f"Error: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        # Test invalid authentication
        try:
            invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
            response = self.session.get(f"{API_BASE}/auth/me", headers=invalid_headers, timeout=10)
            
            if response.status_code == 401:
                self.log_test("Error Handling - Invalid Token", "PASS", 
                            "Invalid token correctly rejected with 401")
            else:
                self.log_test("Error Handling - Invalid Token", "FAIL", 
                            f"Expected 401, got HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Error Handling - Invalid Token", "FAIL", f"Error: {str(e)}")
        
        # Test creating blog with invalid data
        if self.tokens.get("admin"):
            admin_headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            try:
                invalid_blog_data = {
                    "title": "",  # Empty title should fail
                    "content": "Test content"
                    # Missing required category_id
                }
                
                response = self.session.post(
                    f"{API_BASE}/blogs",
                    json=invalid_blog_data,
                    headers=admin_headers,
                    timeout=10
                )
                
                if response.status_code == 422:
                    self.log_test("Error Handling - Invalid Blog Data", "PASS", 
                                "Invalid blog data correctly rejected with 422")
                else:
                    self.log_test("Error Handling - Invalid Blog Data", "FAIL", 
                                f"Expected 422, got HTTP {response.status_code}")
            except Exception as e:
                self.log_test("Error Handling - Invalid Blog Data", "FAIL", f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting MarketMindAI Backend Testing Suite")
        print(f"📡 Testing backend at: {BACKEND_URL}")
        print("=" * 60)
        
        # Run tests in order
        self.test_health_endpoint()
        self.test_authentication()
        self.test_protected_routes()
        self.test_blog_crud_operations()
        self.test_tool_comparison_system()
        self.test_file_upload_system()
        self.test_core_api_endpoints()
        self.test_error_handling()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped = len([r for r in self.test_results if r["status"] == "SKIP"])
        
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"⚠️ SKIPPED: {skipped}")
        print(f"📈 TOTAL: {len(self.test_results)}")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   • {result['test']}: {result['message']}")
        
        print(f"\n🎯 SUCCESS RATE: {(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "N/A")
        
        return {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "total": len(self.test_results),
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()