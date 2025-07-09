"""
Comprehensive Super Admin Tools Testing Module
==============================================

This module contains comprehensive tests for Super Admin functionality related to tools:
1. Tools CRUD Operations 
2. Bulk Tools Upload
3. Tools reflection on Discover Page
4. Data validation and error handling
5. Performance testing

Author: MarketMindAI Testing Suite
Version: 1.0.0
"""

import pytest
import requests
import json
import csv
import io
import os
import uuid
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime
import time

# Test Configuration
class TestConfig:
    """Test configuration and constants"""
    BACKEND_URL = os.getenv("REACT_APP_BACKEND_URL", "http://localhost:8001")
    FRONTEND_URL = os.getenv("REACT_APP_FRONTEND_URL", "http://localhost:3000")
    
    # Test credentials
    SUPER_ADMIN_EMAIL = "superadmin@marketmindai.com"
    SUPER_ADMIN_PASSWORD = "superadmin123"
    ADMIN_EMAIL = "admin@marketmindai.com"
    ADMIN_PASSWORD = "admin123"
    USER_EMAIL = "user@marketmindai.com"
    USER_PASSWORD = "password123"
    
    # Test timeouts
    REQUEST_TIMEOUT = 30
    DISCOVER_PAGE_LOAD_TIMEOUT = 10

class TestClient:
    """HTTP client for making API requests"""
    
    def __init__(self, base_url: str = TestConfig.BACKEND_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = TestConfig.REQUEST_TIMEOUT
    
    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with proper error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            raise Exception(f"Request failed: {e}")
    
    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("POST", endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("PUT", endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("DELETE", endpoint, **kwargs)

class AuthManager:
    """Authentication manager for different user types"""
    
    def __init__(self, client: TestClient):
        self.client = client
        self.tokens = {}
    
    def login(self, email: str, password: str) -> str:
        """Login and return token"""
        response = self.client.post("/api/auth/login", json={
            "email": email,
            "password": password
        })
        
        if response.status_code != 200:
            raise Exception(f"Login failed for {email}: {response.text}")
        
        return response.json()["access_token"]
    
    def get_super_admin_token(self) -> str:
        """Get super admin token"""
        if "super_admin" not in self.tokens:
            self.tokens["super_admin"] = self.login(
                TestConfig.SUPER_ADMIN_EMAIL, 
                TestConfig.SUPER_ADMIN_PASSWORD
            )
        return self.tokens["super_admin"]
    
    def get_admin_token(self) -> str:
        """Get admin token"""
        if "admin" not in self.tokens:
            self.tokens["admin"] = self.login(
                TestConfig.ADMIN_EMAIL, 
                TestConfig.ADMIN_PASSWORD
            )
        return self.tokens["admin"]
    
    def get_user_token(self) -> str:
        """Get regular user token"""
        if "user" not in self.tokens:
            self.tokens["user"] = self.login(
                TestConfig.USER_EMAIL, 
                TestConfig.USER_PASSWORD
            )
        return self.tokens["user"]
    
    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}

class TestDataGenerator:
    """Generate test data for tools"""
    
    @staticmethod
    def generate_tool_data(name_suffix: str = None) -> Dict[str, Any]:
        """Generate valid tool data"""
        suffix = name_suffix or str(uuid.uuid4())[:8]
        return {
            "name": f"Test Tool {suffix}",
            "description": f"Test description for tool {suffix}",
            "short_description": f"Short description for {suffix}",
            "website_url": f"https://testtool{suffix}.com",
            "pricing_model": "Freemium",
            "pricing_details": "Free tier available, paid plans starting from $10/month",
            "features": "Feature 1, Feature 2, Feature 3",
            "target_audience": "Small Business, Enterprise",
            "company_size": "SMB",
            "integrations": "Slack, Microsoft Teams, Google Workspace",
            "logo_url": f"https://testtool{suffix}.com/logo.png",
            "screenshots": "screenshot1.png, screenshot2.png",
            "video_url": f"https://testtool{suffix}.com/demo.mp4",
            "industry": "Technology",
            "employee_size": "11-50",
            "revenue_range": "1M-10M",
            "location": "San Francisco",
            "is_hot": False,
            "is_featured": False,
            "meta_title": f"Test Tool {suffix} - Best Tool for Testing",
            "meta_description": f"Test Tool {suffix} description for SEO",
            "slug": f"test-tool-{suffix}"
        }
    
    @staticmethod
    def generate_csv_data(num_tools: int = 5) -> str:
        """Generate CSV data for bulk upload"""
        headers = [
            "name", "description", "short_description", "website_url", 
            "pricing_model", "pricing_details", "features", "target_audience",
            "company_size", "integrations", "logo_url", "screenshots", 
            "video_url", "industry", "employee_size", "revenue_range", 
            "location", "is_hot", "is_featured", "meta_title", 
            "meta_description", "slug"
        ]
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        for i in range(num_tools):
            tool_data = TestDataGenerator.generate_tool_data(f"csv-{i+1}")
            # Remove category_id as it needs to be set dynamically
            tool_data.pop("category_id", None)
            writer.writerow(tool_data)
        
        return output.getvalue()

class SuperAdminToolsTest:
    """Main test class for Super Admin tools functionality"""
    
    def __init__(self):
        self.client = TestClient()
        self.auth = AuthManager(self.client)
        self.test_data = TestDataGenerator()
        self.created_tools = []
        self.test_categories = []
    
    def setup_test_environment(self):
        """Setup test environment"""
        print("Setting up test environment...")
        
        # Get super admin token
        try:
            self.super_admin_token = self.auth.get_super_admin_token()
            print("✅ Super admin authentication successful")
        except Exception as e:
            print(f"❌ Super admin authentication failed: {e}")
            raise
        
        # Get test categories
        try:
            response = self.client.get("/api/categories")
            if response.status_code == 200:
                self.test_categories = response.json()
                print(f"✅ Found {len(self.test_categories)} categories")
            else:
                print(f"❌ Failed to get categories: {response.text}")
        except Exception as e:
            print(f"❌ Error getting categories: {e}")
    
    def cleanup_test_environment(self):
        """Cleanup test environment"""
        print("Cleaning up test environment...")
        
        # Delete created tools
        for tool_id in self.created_tools:
            try:
                response = self.client.delete(
                    f"/api/tools/{tool_id}",
                    headers=self.auth.get_auth_headers(self.super_admin_token)
                )
                if response.status_code == 200:
                    print(f"✅ Deleted tool {tool_id}")
                else:
                    print(f"❌ Failed to delete tool {tool_id}: {response.text}")
            except Exception as e:
                print(f"❌ Error deleting tool {tool_id}: {e}")
        
        self.created_tools.clear()

    def test_tool_crud_operations(self) -> bool:
        """Test CRUD operations for tools"""
        print("\n" + "="*80)
        print("TESTING TOOL CRUD OPERATIONS")
        print("="*80)
        
        if not self.test_categories:
            print("❌ No categories available for testing")
            return False
        
        category_id = self.test_categories[0]["id"]
        
        # Test CREATE operation
        print("\n--- Testing CREATE Tool ---")
        tool_data = self.test_data.generate_tool_data("crud-test")
        tool_data["category_id"] = category_id
        
        response = self.client.post(
            "/api/tools",
            json=tool_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        if response.status_code != 200:
            print(f"❌ CREATE failed: {response.text}")
            return False
        
        created_tool = response.json()
        tool_id = created_tool["id"]
        self.created_tools.append(tool_id)
        
        print(f"✅ CREATE successful - Tool ID: {tool_id}")
        
        # Test READ operation
        print("\n--- Testing READ Tool ---")
        response = self.client.get(f"/api/tools/{tool_id}")
        
        if response.status_code != 200:
            print(f"❌ READ failed: {response.text}")
            return False
        
        retrieved_tool = response.json()
        print(f"✅ READ successful - Tool Name: {retrieved_tool['name']}")
        
        # Test UPDATE operation
        print("\n--- Testing UPDATE Tool ---")
        update_data = {
            "name": "Updated Test Tool",
            "description": "Updated description",
            "pricing_model": "Paid"
        }
        
        response = self.client.put(
            f"/api/tools/{tool_id}",
            json=update_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        if response.status_code != 200:
            print(f"❌ UPDATE failed: {response.text}")
            return False
        
        updated_tool = response.json()
        print(f"✅ UPDATE successful - New Name: {updated_tool['name']}")
        
        # Test LIST operation
        print("\n--- Testing LIST Tools ---")
        response = self.client.get("/api/tools")
        
        if response.status_code != 200:
            print(f"❌ LIST failed: {response.text}")
            return False
        
        tools_list = response.json()
        print(f"✅ LIST successful - Found {len(tools_list)} tools")
        
        # Test DELETE operation
        print("\n--- Testing DELETE Tool ---")
        response = self.client.delete(
            f"/api/tools/{tool_id}",
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        if response.status_code != 200:
            print(f"❌ DELETE failed: {response.text}")
            return False
        
        print(f"✅ DELETE successful - Tool {tool_id} deleted")
        self.created_tools.remove(tool_id)
        
        # Verify deletion
        response = self.client.get(f"/api/tools/{tool_id}")
        if response.status_code == 404:
            print("✅ DELETE verification successful - Tool not found")
        else:
            print(f"❌ DELETE verification failed - Tool still exists")
            return False
        
        print("\n✅ ALL CRUD OPERATIONS PASSED")
        return True

    def test_bulk_upload_tools(self) -> bool:
        """Test bulk upload functionality"""
        print("\n" + "="*80)
        print("TESTING BULK UPLOAD TOOLS")
        print("="*80)
        
        if not self.test_categories:
            print("❌ No categories available for testing")
            return False
        
        category_id = self.test_categories[0]["id"]
        
        # Generate CSV data
        csv_data = self.test_data.generate_csv_data(3)
        
        # Add category_id to CSV data
        csv_lines = csv_data.split('\n')
        headers = csv_lines[0].split(',')
        
        # Add category_id to headers if not present
        if 'category_id' not in headers:
            headers.append('category_id')
            csv_lines[0] = ','.join(headers)
            
            # Add category_id to each data row
            for i in range(1, len(csv_lines)):
                if csv_lines[i].strip():
                    csv_lines[i] += f",{category_id}"
        
        modified_csv = '\n'.join(csv_lines)
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            tmp_file.write(modified_csv)
            tmp_file_path = tmp_file.name
        
        try:
            # Test bulk upload
            print("\n--- Testing Bulk Upload ---")
            with open(tmp_file_path, 'rb') as file:
                response = self.client.post(
                    "/api/tools/bulk-upload",
                    files={"file": ("test_tools.csv", file, "text/csv")},
                    headers=self.auth.get_auth_headers(self.super_admin_token)
                )
            
            if response.status_code != 200:
                print(f"❌ Bulk upload failed: {response.text}")
                return False
            
            upload_result = response.json()
            created_count = upload_result.get("created_count", 0)
            created_tools = upload_result.get("created_tools", [])
            errors = upload_result.get("errors", [])
            
            print(f"✅ Bulk upload successful - Created {created_count} tools")
            print(f"Created tools: {created_tools}")
            
            if errors:
                print(f"Errors: {errors}")
            
            # Store created tool IDs for cleanup (we need to get them from database)
            response = self.client.get("/api/tools")
            if response.status_code == 200:
                all_tools = response.json()
                for tool in all_tools:
                    if tool["name"] in created_tools:
                        self.created_tools.append(tool["id"])
            
            return created_count > 0
            
        finally:
            # Clean up temp file
            os.unlink(tmp_file_path)

    def test_csv_template_download(self) -> bool:
        """Test CSV template download"""
        print("\n" + "="*80)
        print("TESTING CSV TEMPLATE DOWNLOAD")
        print("="*80)
        
        print("\n--- Testing CSV Template Download ---")
        response = self.client.get(
            "/api/admin/tools/sample-csv",
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        if response.status_code != 200:
            print(f"❌ CSV template download failed: {response.text}")
            return False
        
        # Check Content-Type header
        content_type = response.headers.get('Content-Type', '')
        if 'text/csv' not in content_type:
            print(f"❌ Invalid content type: {content_type}")
            return False
        
        print(f"✅ CSV template download successful")
        print(f"Content-Type: {content_type}")
        print(f"Content length: {len(response.content)} bytes")
        
        return True

    def test_tools_on_discover_page(self) -> bool:
        """Test if tools appear on discover page"""
        print("\n" + "="*80)
        print("TESTING TOOLS ON DISCOVER PAGE")
        print("="*80)
        
        # First create a test tool
        if not self.test_categories:
            print("❌ No categories available for testing")
            return False
        
        category_id = self.test_categories[0]["id"]
        
        print("\n--- Creating Test Tool ---")
        tool_data = self.test_data.generate_tool_data("discover-test")
        tool_data["category_id"] = category_id
        tool_data["is_featured"] = True  # Make it featured for easy identification
        
        response = self.client.post(
            "/api/tools",
            json=tool_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to create test tool: {response.text}")
            return False
        
        created_tool = response.json()
        tool_id = created_tool["id"]
        tool_name = created_tool["name"]
        self.created_tools.append(tool_id)
        
        print(f"✅ Created test tool: {tool_name}")
        
        # Test tools search endpoint (used by discover page)
        print("\n--- Testing Tools Search Endpoint ---")
        response = self.client.get("/api/tools/search")
        
        if response.status_code != 200:
            print(f"❌ Tools search failed: {response.text}")
            return False
        
        search_result = response.json()
        tools = search_result.get("tools", [])
        
        # Check if our tool appears in the results
        tool_found = any(tool["id"] == tool_id for tool in tools)
        
        if tool_found:
            print(f"✅ Tool found in search results")
        else:
            print(f"❌ Tool not found in search results")
            return False
        
        # Test featured tools endpoint
        print("\n--- Testing Tools Analytics Endpoint ---")
        response = self.client.get("/api/tools/analytics")
        
        if response.status_code != 200:
            print(f"❌ Tools analytics failed: {response.text}")
            return False
        
        analytics_result = response.json()
        featured_tools = analytics_result.get("featured_tools", [])
        
        # Check if our featured tool appears in featured tools
        featured_tool_found = any(tool["id"] == tool_id for tool in featured_tools)
        
        if featured_tool_found:
            print(f"✅ Featured tool found in analytics")
        else:
            print(f"❌ Featured tool not found in analytics")
            return False
        
        print("\n✅ ALL DISCOVER PAGE TESTS PASSED")
        return True

    def test_authorization_and_permissions(self) -> bool:
        """Test authorization and permissions"""
        print("\n" + "="*80)
        print("TESTING AUTHORIZATION AND PERMISSIONS")
        print("="*80)
        
        if not self.test_categories:
            print("❌ No categories available for testing")
            return False
        
        category_id = self.test_categories[0]["id"]
        tool_data = self.test_data.generate_tool_data("auth-test")
        tool_data["category_id"] = category_id
        
        # Test without authentication
        print("\n--- Testing Without Authentication ---")
        response = self.client.post("/api/tools", json=tool_data)
        
        if response.status_code == 401:
            print("✅ Unauthorized access properly blocked")
        else:
            print(f"❌ Unauthorized access not blocked: {response.status_code}")
            return False
        
        # Test with regular user (should fail)
        print("\n--- Testing With Regular User ---")
        try:
            user_token = self.auth.get_user_token()
            response = self.client.post(
                "/api/tools",
                json=tool_data,
                headers=self.auth.get_auth_headers(user_token)
            )
            
            if response.status_code == 403:
                print("✅ Regular user access properly blocked")
            else:
                print(f"❌ Regular user access not blocked: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error testing regular user access: {e}")
            return False
        
        # Test with admin user (should succeed)
        print("\n--- Testing With Admin User ---")
        try:
            admin_token = self.auth.get_admin_token()
            response = self.client.post(
                "/api/tools",
                json=tool_data,
                headers=self.auth.get_auth_headers(admin_token)
            )
            
            if response.status_code == 200:
                print("✅ Admin user access allowed")
                # Clean up created tool
                tool_id = response.json()["id"]
                self.created_tools.append(tool_id)
            else:
                print(f"❌ Admin user access blocked: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error testing admin user access: {e}")
            return False
        
        print("\n✅ ALL AUTHORIZATION TESTS PASSED")
        return True

    def test_data_validation(self) -> bool:
        """Test data validation"""
        print("\n" + "="*80)
        print("TESTING DATA VALIDATION")
        print("="*80)
        
        if not self.test_categories:
            print("❌ No categories available for testing")
            return False
        
        category_id = self.test_categories[0]["id"]
        
        # Test with missing required fields
        print("\n--- Testing Missing Required Fields ---")
        invalid_data = {
            "description": "Test description"
            # Missing name, category_id, slug
        }
        
        response = self.client.post(
            "/api/tools",
            json=invalid_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        if response.status_code == 422:
            print("✅ Missing required fields properly validated")
        else:
            print(f"❌ Missing required fields not validated: {response.status_code}")
            return False
        
        # Test with invalid category_id
        print("\n--- Testing Invalid Category ID ---")
        invalid_data = self.test_data.generate_tool_data("validation-test")
        invalid_data["category_id"] = "invalid-category-id"
        
        response = self.client.post(
            "/api/tools",
            json=invalid_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        if response.status_code in [400, 422]:
            print("✅ Invalid category ID properly validated")
        else:
            print(f"❌ Invalid category ID not validated: {response.status_code}")
            # This might still succeed if foreign key constraint is not enforced
            if response.status_code == 200:
                tool_id = response.json()["id"]
                self.created_tools.append(tool_id)
            return False
        
        print("\n✅ ALL DATA VALIDATION TESTS PASSED")
        return True

    def run_all_tests(self) -> bool:
        """Run all tests"""
        print("\n" + "="*100)
        print("SUPER ADMIN TOOLS COMPREHENSIVE TEST SUITE")
        print("="*100)
        
        try:
            # Setup
            self.setup_test_environment()
            
            # Run all tests
            test_results = []
            
            test_results.append(("CRUD Operations", self.test_tool_crud_operations()))
            test_results.append(("Bulk Upload", self.test_bulk_upload_tools()))
            test_results.append(("CSV Template", self.test_csv_template_download()))
            test_results.append(("Discover Page", self.test_tools_on_discover_page()))
            test_results.append(("Authorization", self.test_authorization_and_permissions()))
            test_results.append(("Data Validation", self.test_data_validation()))
            
            # Print results summary
            print("\n" + "="*100)
            print("TEST RESULTS SUMMARY")
            print("="*100)
            
            passed = 0
            failed = 0
            
            for test_name, result in test_results:
                status = "✅ PASSED" if result else "❌ FAILED"
                print(f"{test_name:<20} : {status}")
                if result:
                    passed += 1
                else:
                    failed += 1
            
            print(f"\nTotal Tests: {len(test_results)}")
            print(f"Passed: {passed}")
            print(f"Failed: {failed}")
            
            overall_success = failed == 0
            print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
            
            return overall_success
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return False
        finally:
            # Cleanup
            self.cleanup_test_environment()

def main():
    """Main function to run tests"""
    test_suite = SuperAdminToolsTest()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)

if __name__ == "__main__":
    main()