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
BACKEND_URL = "https://6ce9bd2c-20ae-4eeb-a678-dabf40be8ee0.preview.emergentagent.com"
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
                # First get available tools using search endpoint
                tools_response = self.session.get(f"{API_BASE}/tools/search?limit=10", timeout=10)
                if tools_response.status_code == 200:
                    tools_data = tools_response.json()
                    tools = tools_data.get("tools", [])
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
    
    def test_tool_assignment_endpoints(self):
        """Test new tool assignment endpoints as requested in review request"""
        if not self.tokens.get("superadmin"):
            self.log_test("Tool Assignment", "SKIP", "No superadmin token available")
            return
            
        superadmin_headers = {"Authorization": f"Bearer {self.tokens['superadmin']}"}
        
        # First, get available tools and admins for testing
        try:
            # Get tools using search endpoint
            tools_response = self.session.get(f"{API_BASE}/tools/search?limit=10", timeout=10)
            if tools_response.status_code != 200:
                self.log_test("Tool Assignment - Setup", "FAIL", "Could not retrieve tools for testing")
                return
            
            tools_data = tools_response.json()
            tools = tools_data.get("tools", [])
            if not tools:
                self.log_test("Tool Assignment - Setup", "FAIL", "No tools available for testing")
                return
            
            test_tool_id = tools[0]["id"]
            test_tool_name = tools[0]["name"]
            
            # Get admin user ID (we know admin exists from authentication test)
            admin_id = None
            if self.tokens.get("admin"):
                admin_me_response = self.session.get(
                    f"{API_BASE}/auth/me", 
                    headers={"Authorization": f"Bearer {self.tokens['admin']}"},
                    timeout=10
                )
                if admin_me_response.status_code == 200:
                    admin_data = admin_me_response.json()
                    admin_id = admin_data.get("id")
            
            if not admin_id:
                self.log_test("Tool Assignment - Setup", "FAIL", "Could not get admin ID for testing")
                return
                
            self.log_test("Tool Assignment - Setup", "PASS", 
                        f"Using tool '{test_tool_name}' and admin ID '{admin_id}' for testing")
            
        except Exception as e:
            self.log_test("Tool Assignment - Setup", "FAIL", f"Setup error: {str(e)}")
            return
        
        # Test 1: POST /api/admin/tools/{tool_id}/assign - Assign tool to admin (Super Admin only)
        try:
            assignment_data = {"admin_id": admin_id}
            
            response = self.session.post(
                f"{API_BASE}/admin/tools/{test_tool_id}/assign",
                json=assignment_data,
                headers=superadmin_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                assignment_result = response.json()
                if (assignment_result.get("message") == "Tool assigned successfully" and
                    assignment_result.get("tool_id") == test_tool_id and
                    assignment_result.get("admin_id") == admin_id):
                    self.log_test("Tool Assignment - Assign Tool", "PASS", 
                                f"Tool '{test_tool_name}' successfully assigned to admin")
                else:
                    self.log_test("Tool Assignment - Assign Tool", "FAIL", 
                                f"Invalid response format: {assignment_result}")
            else:
                self.log_test("Tool Assignment - Assign Tool", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Tool Assignment - Assign Tool", "FAIL", f"Error: {str(e)}")
        
        # Test 2: GET /api/admin/tools/assignments - Get tool assignments
        try:
            response = self.session.get(
                f"{API_BASE}/admin/tools/assignments",
                headers=superadmin_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                assignments = response.json()
                if isinstance(assignments, list):
                    # Check if our assignment is in the list
                    found_assignment = any(
                        assignment.get("tool_id") == test_tool_id and 
                        assignment.get("admin_id") == admin_id
                        for assignment in assignments
                    )
                    if found_assignment:
                        self.log_test("Tool Assignment - Get Assignments", "PASS", 
                                    f"Retrieved {len(assignments)} assignments, including our test assignment")
                    else:
                        self.log_test("Tool Assignment - Get Assignments", "FAIL", 
                                    "Test assignment not found in assignments list")
                else:
                    self.log_test("Tool Assignment - Get Assignments", "FAIL", 
                                "Response is not a list")
            else:
                self.log_test("Tool Assignment - Get Assignments", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Tool Assignment - Get Assignments", "FAIL", f"Error: {str(e)}")
        
        # Test 3: GET /api/admin/tools/assigned - Get tools assigned to current admin (test with admin token)
        if self.tokens.get("admin"):
            admin_headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            try:
                response = self.session.get(
                    f"{API_BASE}/admin/tools/assigned",
                    headers=admin_headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    assigned_tools = response.json()
                    if isinstance(assigned_tools, list):
                        # Check if our assigned tool is in the list
                        found_tool = any(tool.get("id") == test_tool_id for tool in assigned_tools)
                        if found_tool:
                            self.log_test("Tool Assignment - Get Assigned Tools", "PASS", 
                                        f"Admin can see {len(assigned_tools)} assigned tools, including test tool")
                        else:
                            self.log_test("Tool Assignment - Get Assigned Tools", "FAIL", 
                                        "Test tool not found in admin's assigned tools")
                    else:
                        self.log_test("Tool Assignment - Get Assigned Tools", "FAIL", 
                                    "Response is not a list")
                else:
                    self.log_test("Tool Assignment - Get Assigned Tools", "FAIL", 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Tool Assignment - Get Assigned Tools", "FAIL", f"Error: {str(e)}")
        
        # Test 4: DELETE /api/admin/tools/{tool_id}/assign - Unassign tool from admin (Super Admin only)
        try:
            response = self.session.delete(
                f"{API_BASE}/admin/tools/{test_tool_id}/assign",
                headers=superadmin_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                unassign_result = response.json()
                if (unassign_result.get("message") == "Tool unassigned successfully" and
                    unassign_result.get("tool_id") == test_tool_id):
                    self.log_test("Tool Assignment - Unassign Tool", "PASS", 
                                f"Tool '{test_tool_name}' successfully unassigned from admin")
                else:
                    self.log_test("Tool Assignment - Unassign Tool", "FAIL", 
                                f"Invalid response format: {unassign_result}")
            else:
                self.log_test("Tool Assignment - Unassign Tool", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Tool Assignment - Unassign Tool", "FAIL", f"Error: {str(e)}")
        
        # Test 5: Error cases - Try to assign as regular admin (should fail)
        if self.tokens.get("admin"):
            admin_headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            try:
                assignment_data = {"admin_id": admin_id}
                
                response = self.session.post(
                    f"{API_BASE}/admin/tools/{test_tool_id}/assign",
                    json=assignment_data,
                    headers=admin_headers,
                    timeout=10
                )
                
                if response.status_code == 403:
                    self.log_test("Tool Assignment - Admin Access Denied", "PASS", 
                                "Regular admin correctly denied access to assignment endpoint")
                else:
                    self.log_test("Tool Assignment - Admin Access Denied", "FAIL", 
                                f"Expected 403, got HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test("Tool Assignment - Admin Access Denied", "FAIL", f"Error: {str(e)}")
        
        # Test 6: Error cases - Try to assign to non-existent admin
        try:
            fake_admin_id = "00000000-0000-0000-0000-000000000000"
            assignment_data = {"admin_id": fake_admin_id}
            
            response = self.session.post(
                f"{API_BASE}/admin/tools/{test_tool_id}/assign",
                json=assignment_data,
                headers=superadmin_headers,
                timeout=10
            )
            
            if response.status_code == 404:
                self.log_test("Tool Assignment - Non-existent Admin", "PASS", 
                            "Assignment to non-existent admin correctly rejected with 404")
            else:
                self.log_test("Tool Assignment - Non-existent Admin", "FAIL", 
                            f"Expected 404, got HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Tool Assignment - Non-existent Admin", "FAIL", f"Error: {str(e)}")
        
        # Test 7: Error cases - Try to assign non-existent tool
        try:
            fake_tool_id = "00000000-0000-0000-0000-000000000000"
            assignment_data = {"admin_id": admin_id}
            
            response = self.session.post(
                f"{API_BASE}/admin/tools/{fake_tool_id}/assign",
                json=assignment_data,
                headers=superadmin_headers,
                timeout=10
            )
            
            if response.status_code == 404:
                self.log_test("Tool Assignment - Non-existent Tool", "PASS", 
                            "Assignment of non-existent tool correctly rejected with 404")
            else:
                self.log_test("Tool Assignment - Non-existent Tool", "FAIL", 
                            f"Expected 404, got HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Tool Assignment - Non-existent Tool", "FAIL", f"Error: {str(e)}")

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
    
    def test_blog_crud_all_users(self):
        """Test blog CRUD operations for all user types as requested in review request"""
        # Test with all user types
        for user_type in ["user", "admin", "superadmin"]:
            if not self.tokens.get(user_type):
                self.log_test(f"Blog CRUD - {user_type.title()}", "SKIP", f"No {user_type} token available")
                continue
                
            headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
            
            # Get categories for blog creation
            try:
                cat_response = self.session.get(f"{API_BASE}/categories", timeout=10)
                if cat_response.status_code != 200:
                    self.log_test(f"Blog CRUD - {user_type.title()} Setup", "FAIL", "Could not retrieve categories")
                    continue
                
                categories = cat_response.json()
                if not categories:
                    self.log_test(f"Blog CRUD - {user_type.title()} Setup", "FAIL", "No categories available")
                    continue
                    
                category_id = categories[0]["id"]
                
            except Exception as e:
                self.log_test(f"Blog CRUD - {user_type.title()} Setup", "FAIL", f"Setup error: {str(e)}")
                continue
            
            # Test blog creation
            try:
                blog_data = {
                    "title": f"Test Blog by {user_type.title()} - {int(time.time())}",
                    "content": f"This is test content for debugging blog functionality by {user_type} user type. Testing comprehensive CRUD operations.",
                    "category_id": category_id,
                    "slug": f"test-blog-{user_type}-{int(time.time())}",
                    "status": "published",
                    "meta_description": f"Test blog created by {user_type} for API testing"
                }
                
                response = self.session.post(
                    f"{API_BASE}/blogs",
                    json=blog_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 201 or response.status_code == 200:
                    blog = response.json()
                    blog_id = blog.get("id")
                    self.log_test(f"Blog Creation - {user_type.title()}", "PASS", 
                                f"Blog created successfully with ID: {blog_id}")
                    
                    # Test blog update
                    if blog_id:
                        try:
                            update_data = {
                                "title": f"Updated Test Blog by {user_type.title()}",
                                "content": f"Updated content by {user_type} user - testing update functionality"
                            }
                            
                            update_response = self.session.put(
                                f"{API_BASE}/blogs/{blog_id}",
                                json=update_data,
                                headers=headers,
                                timeout=10
                            )
                            
                            if update_response.status_code == 200:
                                updated_blog = update_response.json()
                                if updated_blog.get("title") == update_data["title"]:
                                    self.log_test(f"Blog Update - {user_type.title()}", "PASS", 
                                                "Blog updated successfully")
                                else:
                                    self.log_test(f"Blog Update - {user_type.title()}", "FAIL", 
                                                "Blog update data mismatch")
                            else:
                                self.log_test(f"Blog Update - {user_type.title()}", "FAIL", 
                                            f"HTTP {update_response.status_code}: {update_response.text}")
                        except Exception as e:
                            self.log_test(f"Blog Update - {user_type.title()}", "FAIL", f"Error: {str(e)}")
                        
                        # Test blog deletion
                        try:
                            delete_response = self.session.delete(
                                f"{API_BASE}/blogs/{blog_id}",
                                headers=headers,
                                timeout=10
                            )
                            
                            if delete_response.status_code == 200:
                                self.log_test(f"Blog Delete - {user_type.title()}", "PASS", 
                                            "Blog deleted successfully")
                            else:
                                self.log_test(f"Blog Delete - {user_type.title()}", "FAIL", 
                                            f"HTTP {delete_response.status_code}: {delete_response.text}")
                        except Exception as e:
                            self.log_test(f"Blog Delete - {user_type.title()}", "FAIL", f"Error: {str(e)}")
                else:
                    self.log_test(f"Blog Creation - {user_type.title()}", "FAIL", 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Blog Creation - {user_type.title()}", "FAIL", f"Error: {str(e)}")

    def test_blog_like_system(self):
        """Test blog like system functionality as requested in review request"""
        # First create a test blog to like
        if not self.tokens.get("admin"):
            self.log_test("Blog Like System", "SKIP", "No admin token available")
            return
            
        admin_headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        
        # Get categories for blog creation
        try:
            cat_response = self.session.get(f"{API_BASE}/categories", timeout=10)
            if cat_response.status_code != 200:
                self.log_test("Blog Like System - Setup", "FAIL", "Could not retrieve categories")
                return
            
            categories = cat_response.json()
            if not categories:
                self.log_test("Blog Like System - Setup", "FAIL", "No categories available")
                return
                
            category_id = categories[0]["id"]
            
        except Exception as e:
            self.log_test("Blog Like System - Setup", "FAIL", f"Setup error: {str(e)}")
            return
        
        # Create test blog
        try:
            blog_data = {
                "title": f"Test Blog for Like System - {int(time.time())}",
                "content": "This blog is created specifically for testing the like system functionality.",
                "category_id": category_id,
                "slug": f"test-blog-likes-{int(time.time())}",
                "status": "published"
            }
            
            response = self.session.post(
                f"{API_BASE}/blogs",
                json=blog_data,
                headers=admin_headers,
                timeout=10
            )
            
            if response.status_code != 201 and response.status_code != 200:
                self.log_test("Blog Like System - Blog Creation", "FAIL", 
                            f"Could not create test blog: HTTP {response.status_code}")
                return
            
            blog = response.json()
            blog_id = blog.get("id")
            
            if not blog_id:
                self.log_test("Blog Like System - Blog Creation", "FAIL", "No blog ID returned")
                return
                
            self.log_test("Blog Like System - Blog Creation", "PASS", f"Test blog created with ID: {blog_id}")
            
        except Exception as e:
            self.log_test("Blog Like System - Blog Creation", "FAIL", f"Error: {str(e)}")
            return
        
        # Test like functionality with different user types
        for user_type in ["user", "admin", "superadmin"]:
            if not self.tokens.get(user_type):
                continue
                
            headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
            
            # Test liking a blog
            try:
                like_response = self.session.post(
                    f"{API_BASE}/blogs/{blog_id}/like",
                    headers=headers,
                    timeout=10
                )
                
                if like_response.status_code == 200:
                    like_data = like_response.json()
                    if "action" in like_data and "likes" in like_data and "user_liked" in like_data:
                        action = like_data.get("action")
                        likes_count = like_data.get("likes")
                        user_liked = like_data.get("user_liked")
                        
                        self.log_test(f"Blog Like - {user_type.title()}", "PASS", 
                                    f"Like action: {action}, Total likes: {likes_count}, User liked: {user_liked}")
                        
                        # Test like status check
                        try:
                            status_response = self.session.get(
                                f"{API_BASE}/blogs/{blog_id}/like-status",
                                headers=headers,
                                timeout=10
                            )
                            
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                if "user_liked" in status_data and "total_likes" in status_data:
                                    self.log_test(f"Blog Like Status - {user_type.title()}", "PASS", 
                                                f"Status check successful: User liked: {status_data.get('user_liked')}, Total: {status_data.get('total_likes')}")
                                else:
                                    self.log_test(f"Blog Like Status - {user_type.title()}", "FAIL", 
                                                "Missing required fields in status response")
                            else:
                                self.log_test(f"Blog Like Status - {user_type.title()}", "FAIL", 
                                            f"HTTP {status_response.status_code}: {status_response.text}")
                        except Exception as e:
                            self.log_test(f"Blog Like Status - {user_type.title()}", "FAIL", f"Error: {str(e)}")
                        
                        # Test unliking (toggle functionality)
                        try:
                            unlike_response = self.session.post(
                                f"{API_BASE}/blogs/{blog_id}/like",
                                headers=headers,
                                timeout=10
                            )
                            
                            if unlike_response.status_code == 200:
                                unlike_data = unlike_response.json()
                                unlike_action = unlike_data.get("action")
                                if unlike_action == "unliked":
                                    self.log_test(f"Blog Unlike - {user_type.title()}", "PASS", 
                                                f"Unlike successful: {unlike_action}")
                                else:
                                    self.log_test(f"Blog Unlike - {user_type.title()}", "FAIL", 
                                                f"Expected 'unliked', got: {unlike_action}")
                            else:
                                self.log_test(f"Blog Unlike - {user_type.title()}", "FAIL", 
                                            f"HTTP {unlike_response.status_code}: {unlike_response.text}")
                        except Exception as e:
                            self.log_test(f"Blog Unlike - {user_type.title()}", "FAIL", f"Error: {str(e)}")
                    else:
                        self.log_test(f"Blog Like - {user_type.title()}", "FAIL", 
                                    "Missing required fields in like response")
                else:
                    self.log_test(f"Blog Like - {user_type.title()}", "FAIL", 
                                f"HTTP {like_response.status_code}: {like_response.text}")
                    
            except Exception as e:
                self.log_test(f"Blog Like - {user_type.title()}", "FAIL", f"Error: {str(e)}")

    def test_review_system(self):
        """Test review system functionality as requested in review request"""
        # Get available tools for testing
        try:
            tools_response = self.session.get(f"{API_BASE}/tools/search?limit=10", timeout=10)
            if tools_response.status_code != 200:
                self.log_test("Review System - Setup", "FAIL", "Could not retrieve tools")
                return
            
            tools_data = tools_response.json()
            tools = tools_data.get("tools", [])
            if not tools:
                self.log_test("Review System - Setup", "FAIL", "No tools available for testing")
                return
                
            test_tool_id = tools[0]["id"]
            test_tool_name = tools[0]["name"]
            
        except Exception as e:
            self.log_test("Review System - Setup", "FAIL", f"Setup error: {str(e)}")
            return
        
        # Test review functionality with different user types
        for user_type in ["user", "admin", "superadmin"]:
            if not self.tokens.get(user_type):
                continue
                
            headers = {"Authorization": f"Bearer {self.tokens[user_type]}"}
            
            # Test creating a review
            try:
                review_data = {
                    "tool_id": test_tool_id,  # Add the missing tool_id field
                    "rating": 5,
                    "title": f"Great tool! - Review by {user_type}",
                    "content": f"This tool works perfectly. Testing review system with {user_type} account.",
                    "pros": "Easy to use, great features",
                    "cons": "None found during testing"
                }
                
                response = self.session.post(
                    f"{API_BASE}/tools/{test_tool_id}/reviews",
                    json=review_data,
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 201 or response.status_code == 200:
                    review = response.json()
                    review_id = review.get("id")
                    self.log_test(f"Review Creation - {user_type.title()}", "PASS", 
                                f"Review created successfully for tool '{test_tool_name}' with ID: {review_id}")
                    
                    # Test review status check
                    try:
                        status_response = self.session.get(
                            f"{API_BASE}/tools/{test_tool_id}/review-status",
                            headers=headers,
                            timeout=10
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            required_fields = ["has_reviewed", "total_reviews", "average_rating"]
                            if all(field in status_data for field in required_fields):
                                self.log_test(f"Review Status - {user_type.title()}", "PASS", 
                                            f"Status check successful: Has reviewed: {status_data.get('has_reviewed')}, Total: {status_data.get('total_reviews')}, Avg: {status_data.get('average_rating')}")
                            else:
                                self.log_test(f"Review Status - {user_type.title()}", "FAIL", 
                                            "Missing required fields in status response")
                        else:
                            self.log_test(f"Review Status - {user_type.title()}", "FAIL", 
                                        f"HTTP {status_response.status_code}: {status_response.text}")
                    except Exception as e:
                        self.log_test(f"Review Status - {user_type.title()}", "FAIL", f"Error: {str(e)}")
                    
                    # Test review update
                    if review_id:
                        try:
                            update_data = {
                                "rating": 4,
                                "title": f"Updated review by {user_type}",
                                "content": f"Updated review content by {user_type} user",
                                "pros": "Still great features",
                                "cons": "Minor issues found"
                            }
                            
                            update_response = self.session.put(
                                f"{API_BASE}/tools/reviews/{review_id}",
                                json=update_data,
                                headers=headers,
                                timeout=10
                            )
                            
                            if update_response.status_code == 200:
                                updated_review = update_response.json()
                                if updated_review.get("title") == update_data["title"]:
                                    self.log_test(f"Review Update - {user_type.title()}", "PASS", 
                                                "Review updated successfully")
                                else:
                                    self.log_test(f"Review Update - {user_type.title()}", "FAIL", 
                                                "Review update data mismatch")
                            else:
                                self.log_test(f"Review Update - {user_type.title()}", "FAIL", 
                                            f"HTTP {update_response.status_code}: {update_response.text}")
                        except Exception as e:
                            self.log_test(f"Review Update - {user_type.title()}", "FAIL", f"Error: {str(e)}")
                        
                        # Test review deletion
                        try:
                            delete_response = self.session.delete(
                                f"{API_BASE}/tools/reviews/{review_id}",
                                headers=headers,
                                timeout=10
                            )
                            
                            if delete_response.status_code == 200:
                                self.log_test(f"Review Delete - {user_type.title()}", "PASS", 
                                            "Review deleted successfully")
                            else:
                                self.log_test(f"Review Delete - {user_type.title()}", "FAIL", 
                                            f"HTTP {delete_response.status_code}: {delete_response.text}")
                        except Exception as e:
                            self.log_test(f"Review Delete - {user_type.title()}", "FAIL", f"Error: {str(e)}")
                elif response.status_code == 400 and "already reviewed" in response.text.lower():
                    # User already has a review for this tool, which is expected behavior
                    self.log_test(f"Review Creation - {user_type.title()}", "PASS", 
                                "Duplicate review correctly prevented (user already reviewed this tool)")
                else:
                    self.log_test(f"Review Creation - {user_type.title()}", "FAIL", 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Review Creation - {user_type.title()}", "FAIL", f"Error: {str(e)}")

    def test_bulk_upload_functionality(self):
        """Test the updated bulk upload functionality for SuperAdmin tools as requested in review request"""
        if not self.tokens.get("superadmin"):
            self.log_test("Bulk Upload", "SKIP", "No superadmin token available")
            return
            
        superadmin_headers = {"Authorization": f"Bearer {self.tokens['superadmin']}"}
        
        # Test 1: CSV Template Download - should show category names and list available categories
        try:
            response = self.session.get(
                f"{API_BASE}/superadmin/tools/sample-csv",
                headers=superadmin_headers,
                timeout=10
            )
            
            if response.status_code == 200:
                csv_content = response.text
                
                # Check if response is CSV format
                if response.headers.get("content-type") == "text/csv":
                    # Check if CSV contains category_name field (not category_id)
                    if "category_name" in csv_content and "category_id" not in csv_content:
                        # Check if available categories are listed at the end
                        if "# Available Categories" in csv_content and "# -" in csv_content:
                            self.log_test("CSV Template - Category Names", "PASS", 
                                        "CSV template correctly shows category names and lists available categories")
                        else:
                            self.log_test("CSV Template - Category Names", "FAIL", 
                                        "CSV template missing available categories list")
                    else:
                        self.log_test("CSV Template - Category Names", "FAIL", 
                                    "CSV template still uses category_id instead of category_name")
                else:
                    self.log_test("CSV Template - Category Names", "FAIL", 
                                f"Wrong content type: {response.headers.get('content-type')}")
            else:
                self.log_test("CSV Template - Category Names", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("CSV Template - Category Names", "FAIL", f"Error: {str(e)}")
        
        # Get available categories for testing
        try:
            cat_response = self.session.get(f"{API_BASE}/categories", timeout=10)
            if cat_response.status_code != 200:
                self.log_test("Bulk Upload - Setup", "FAIL", "Could not retrieve categories for testing")
                return
            
            categories = cat_response.json()
            if not categories:
                self.log_test("Bulk Upload - Setup", "FAIL", "No categories available for testing")
                return
                
            test_category_name = categories[0]["name"]
            test_category_id = categories[0]["id"]
            
        except Exception as e:
            self.log_test("Bulk Upload - Setup", "FAIL", f"Setup error: {str(e)}")
            return
        
        # Test 2: Bulk upload with category names (not IDs) - should work correctly
        try:
            # Create CSV content with category name
            csv_content_with_name = f"""name,description,website_url,pricing_model,category_name,features,integrations
Test Tool Category Name,Test tool uploaded with category name,https://testtool-name.com,Freemium,{test_category_name},"Task management,Collaboration","Slack,Google Drive"
"""
            
            # Create file-like object
            import io
            csv_file = io.BytesIO(csv_content_with_name.encode('utf-8'))
            
            files = {"file": ("test_category_name.csv", csv_file, "text/csv")}
            
            response = self.session.post(
                f"{API_BASE}/superadmin/tools/bulk-upload",
                files=files,
                headers=superadmin_headers,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("total_processed", 0) > 0 and result.get("total_errors", 0) == 0:
                    self.log_test("Bulk Upload - Category Name", "PASS", 
                                f"Successfully uploaded tool using category name '{test_category_name}'")
                else:
                    self.log_test("Bulk Upload - Category Name", "FAIL", 
                                f"Upload failed with errors: {result.get('errors', [])}")
            else:
                self.log_test("Bulk Upload - Category Name", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Bulk Upload - Category Name", "FAIL", f"Error: {str(e)}")
        
        # Test 3: Bulk upload with category IDs (for backward compatibility) - should still work
        try:
            # Create CSV content with category ID
            csv_content_with_id = f"""name,description,website_url,pricing_model,category_id,features,integrations
Test Tool Category ID,Test tool uploaded with category ID,https://testtool-id.com,Paid,{test_category_id},"Project management,Analytics","Zoom,Dropbox"
"""
            
            # Create file-like object
            csv_file = io.BytesIO(csv_content_with_id.encode('utf-8'))
            
            files = {"file": ("test_category_id.csv", csv_file, "text/csv")}
            
            response = self.session.post(
                f"{API_BASE}/superadmin/tools/bulk-upload",
                files=files,
                headers=superadmin_headers,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("total_processed", 0) > 0 and result.get("total_errors", 0) == 0:
                    self.log_test("Bulk Upload - Category ID (Backward Compatibility)", "PASS", 
                                f"Successfully uploaded tool using category ID '{test_category_id}'")
                else:
                    self.log_test("Bulk Upload - Category ID (Backward Compatibility)", "FAIL", 
                                f"Upload failed with errors: {result.get('errors', [])}")
            else:
                self.log_test("Bulk Upload - Category ID (Backward Compatibility)", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Bulk Upload - Category ID (Backward Compatibility)", "FAIL", f"Error: {str(e)}")
        
        # Test 4: Error handling for invalid category names
        try:
            # Create CSV content with invalid category name
            csv_content_invalid_name = """name,description,website_url,pricing_model,category_name,features,integrations
Test Tool Invalid Category,Test tool with invalid category name,https://testtool-invalid.com,Free,NonExistentCategory,"Testing,Validation","API,Database"
"""
            
            # Create file-like object
            csv_file = io.BytesIO(csv_content_invalid_name.encode('utf-8'))
            
            files = {"file": ("test_invalid_category.csv", csv_file, "text/csv")}
            
            response = self.session.post(
                f"{API_BASE}/superadmin/tools/bulk-upload",
                files=files,
                headers=superadmin_headers,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("total_errors", 0) > 0 and "Category name not found" in str(result.get("errors", [])):
                    self.log_test("Bulk Upload - Invalid Category Name", "PASS", 
                                "Correctly rejected upload with invalid category name")
                else:
                    self.log_test("Bulk Upload - Invalid Category Name", "FAIL", 
                                f"Should have rejected invalid category name: {result}")
            else:
                self.log_test("Bulk Upload - Invalid Category Name", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Bulk Upload - Invalid Category Name", "FAIL", f"Error: {str(e)}")
        
        # Test 5: Error handling for missing category information
        try:
            # Create CSV content without category information
            csv_content_no_category = """name,description,website_url,pricing_model,features,integrations
Test Tool No Category,Test tool without category info,https://testtool-nocategory.com,Enterprise,"Advanced features,Support","Custom integrations"
"""
            
            # Create file-like object
            csv_file = io.BytesIO(csv_content_no_category.encode('utf-8'))
            
            files = {"file": ("test_no_category.csv", csv_file, "text/csv")}
            
            response = self.session.post(
                f"{API_BASE}/superadmin/tools/bulk-upload",
                files=files,
                headers=superadmin_headers,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("total_errors", 0) > 0 and ("category_id" in str(result.get("errors", [])) or "category_name" in str(result.get("errors", []))):
                    self.log_test("Bulk Upload - Missing Category", "PASS", 
                                "Correctly rejected upload with missing category information")
                else:
                    self.log_test("Bulk Upload - Missing Category", "FAIL", 
                                f"Should have rejected missing category: {result}")
            else:
                self.log_test("Bulk Upload - Missing Category", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Bulk Upload - Missing Category", "FAIL", f"Error: {str(e)}")
        
        # Test 6: Test case-insensitive category name matching
        try:
            # Create CSV content with different case category name
            csv_content_case_test = f"""name,description,website_url,pricing_model,category_name,features,integrations
Test Tool Case Insensitive,Test tool with different case category name,https://testtool-case.com,Subscription,{test_category_name.upper()},"Case testing,Validation","Testing tools"
"""
            
            # Create file-like object
            csv_file = io.BytesIO(csv_content_case_test.encode('utf-8'))
            
            files = {"file": ("test_case_insensitive.csv", csv_file, "text/csv")}
            
            response = self.session.post(
                f"{API_BASE}/superadmin/tools/bulk-upload",
                files=files,
                headers=superadmin_headers,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("total_processed", 0) > 0 and result.get("total_errors", 0) == 0:
                    self.log_test("Bulk Upload - Case Insensitive Category", "PASS", 
                                f"Successfully uploaded tool using uppercase category name '{test_category_name.upper()}'")
                else:
                    self.log_test("Bulk Upload - Case Insensitive Category", "FAIL", 
                                f"Case insensitive matching failed: {result.get('errors', [])}")
            else:
                self.log_test("Bulk Upload - Case Insensitive Category", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Bulk Upload - Case Insensitive Category", "FAIL", f"Error: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting MarketMindAI Backend Testing Suite - Review Request Focus")
        print(f"📡 Testing backend at: {BACKEND_URL}")
        print("🎯 Focus: Blog CRUD, Blog Likes, Review System for all user types")
        print("=" * 60)
        
        # Run tests in order - prioritizing review request items
        self.test_health_endpoint()
        self.test_authentication()
        self.test_protected_routes()
        
        # Review request specific tests
        print("\n🔍 REVIEW REQUEST SPECIFIC TESTS:")
        print("-" * 40)
        self.test_blog_crud_all_users()  # Test blog CRUD for all user types
        self.test_blog_like_system()     # Test blog like system
        self.test_review_system()        # Test review system
        
        # Additional comprehensive tests
        print("\n📋 ADDITIONAL COMPREHENSIVE TESTS:")
        print("-" * 40)
        self.test_tool_comparison_system()
        self.test_file_upload_system()
        self.test_core_api_endpoints()
        self.test_tool_assignment_endpoints()  # New test for tool assignment endpoints
        self.test_bulk_upload_functionality()  # New test for bulk upload functionality
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