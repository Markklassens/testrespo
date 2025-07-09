"""
Unit Testing Module for Super Admin Tools
=========================================

This module contains focused unit tests for individual components:
1. Data validation tests
2. Schema validation tests  
3. API endpoint unit tests
4. Database operation tests
5. Authentication unit tests

Author: MarketMindAI Testing Suite
Version: 1.0.0
"""

import unittest
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
from test_super_admin_tools import TestClient, AuthManager, TestDataGenerator, TestConfig

class BaseUnitTest(unittest.TestCase):
    """Base unit test class with common setup"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class"""
        cls.client = TestClient()
        cls.auth = AuthManager(cls.client)
        cls.data_generator = TestDataGenerator()
        cls.created_tools = []
        cls.test_categories = []
        
        # Get super admin token
        cls.super_admin_token = cls.auth.get_super_admin_token()
        
        # Get test categories
        response = cls.client.get("/api/categories")
        if response.status_code == 200:
            cls.test_categories = response.json()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test class"""
        # Delete created tools
        for tool_id in cls.created_tools:
            try:
                cls.client.delete(
                    f"/api/tools/{tool_id}",
                    headers=cls.auth.get_auth_headers(cls.super_admin_token)
                )
            except:
                pass
    
    def _create_test_tool(self, **kwargs) -> Dict[str, Any]:
        """Create a test tool and return its data"""
        if not self.test_categories:
            self.skipTest("No categories available for testing")
        
        tool_data = self.data_generator.generate_tool_data()
        tool_data["category_id"] = self.test_categories[0]["id"]
        tool_data.update(kwargs)
        
        response = self.client.post(
            "/api/tools",
            json=tool_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        self.assertEqual(response.status_code, 200)
        
        created_tool = response.json()
        self.created_tools.append(created_tool["id"])
        
        return created_tool

class TestToolCRUDOperations(BaseUnitTest):
    """Unit tests for tool CRUD operations"""
    
    def test_create_tool_valid_data(self):
        """Test creating a tool with valid data"""
        tool_data = self.data_generator.generate_tool_data("unit-test-create")
        tool_data["category_id"] = self.test_categories[0]["id"]
        
        response = self.client.post(
            "/api/tools",
            json=tool_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        self.assertEqual(response.status_code, 200)
        
        created_tool = response.json()
        self.created_tools.append(created_tool["id"])
        
        # Verify response structure
        self.assertIn("id", created_tool)
        self.assertIn("name", created_tool)
        self.assertIn("description", created_tool)
        self.assertIn("category_id", created_tool)
        self.assertIn("created_at", created_tool)
        self.assertIn("last_updated", created_tool)
        
        # Verify data
        self.assertEqual(created_tool["name"], tool_data["name"])
        self.assertEqual(created_tool["description"], tool_data["description"])
        self.assertEqual(created_tool["category_id"], tool_data["category_id"])
    
    def test_create_tool_missing_required_fields(self):
        """Test creating a tool with missing required fields"""
        invalid_data = {
            "description": "Test description"
            # Missing name, category_id, slug
        }
        
        response = self.client.post(
            "/api/tools",
            json=invalid_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        self.assertEqual(response.status_code, 422)
    
    def test_create_tool_invalid_category(self):
        """Test creating a tool with invalid category_id"""
        tool_data = self.data_generator.generate_tool_data("invalid-category")
        tool_data["category_id"] = "invalid-category-id"
        
        response = self.client.post(
            "/api/tools",
            json=tool_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        # Should fail with validation error
        self.assertIn(response.status_code, [400, 422])
    
    def test_read_tool_valid_id(self):
        """Test reading a tool with valid ID"""
        # Create a test tool
        created_tool = self._create_test_tool(name="Unit Test Read Tool")
        
        # Read the tool
        response = self.client.get(f"/api/tools/{created_tool['id']}")
        
        self.assertEqual(response.status_code, 200)
        
        retrieved_tool = response.json()
        self.assertEqual(retrieved_tool["id"], created_tool["id"])
        self.assertEqual(retrieved_tool["name"], created_tool["name"])
        
        # Verify view count increment
        self.assertEqual(retrieved_tool["views"], created_tool["views"] + 1)
    
    def test_read_tool_invalid_id(self):
        """Test reading a tool with invalid ID"""
        response = self.client.get("/api/tools/invalid-tool-id")
        
        self.assertEqual(response.status_code, 404)
    
    def test_update_tool_valid_data(self):
        """Test updating a tool with valid data"""
        # Create a test tool
        created_tool = self._create_test_tool(name="Unit Test Update Tool")
        
        # Update the tool
        update_data = {
            "name": "Updated Unit Test Tool",
            "description": "Updated description",
            "pricing_model": "Paid"
        }
        
        response = self.client.put(
            f"/api/tools/{created_tool['id']}",
            json=update_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        self.assertEqual(response.status_code, 200)
        
        updated_tool = response.json()
        self.assertEqual(updated_tool["name"], update_data["name"])
        self.assertEqual(updated_tool["description"], update_data["description"])
        self.assertEqual(updated_tool["pricing_model"], update_data["pricing_model"])
        
        # Verify unchanged fields
        self.assertEqual(updated_tool["id"], created_tool["id"])
        self.assertEqual(updated_tool["category_id"], created_tool["category_id"])
    
    def test_update_tool_invalid_id(self):
        """Test updating a tool with invalid ID"""
        update_data = {"name": "Updated Tool"}
        
        response = self.client.put(
            "/api/tools/invalid-tool-id",
            json=update_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_delete_tool_valid_id(self):
        """Test deleting a tool with valid ID"""
        # Create a test tool
        created_tool = self._create_test_tool(name="Unit Test Delete Tool")
        
        # Delete the tool
        response = self.client.delete(
            f"/api/tools/{created_tool['id']}",
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify tool is deleted
        response = self.client.get(f"/api/tools/{created_tool['id']}")
        self.assertEqual(response.status_code, 404)
        
        # Remove from cleanup list
        self.created_tools.remove(created_tool["id"])
    
    def test_delete_tool_invalid_id(self):
        """Test deleting a tool with invalid ID"""
        response = self.client.delete(
            "/api/tools/invalid-tool-id",
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_list_tools_default_pagination(self):
        """Test listing tools with default pagination"""
        response = self.client.get("/api/tools")
        
        self.assertEqual(response.status_code, 200)
        
        tools = response.json()
        self.assertIsInstance(tools, list)
        self.assertLessEqual(len(tools), 20)  # Default limit
    
    def test_list_tools_custom_pagination(self):
        """Test listing tools with custom pagination"""
        response = self.client.get("/api/tools?skip=0&limit=5")
        
        self.assertEqual(response.status_code, 200)
        
        tools = response.json()
        self.assertIsInstance(tools, list)
        self.assertLessEqual(len(tools), 5)
    
    def test_list_tools_category_filter(self):
        """Test listing tools with category filter"""
        if not self.test_categories:
            self.skipTest("No categories available for testing")
        
        category_id = self.test_categories[0]["id"]
        response = self.client.get(f"/api/tools?category_id={category_id}")
        
        self.assertEqual(response.status_code, 200)
        
        tools = response.json()
        self.assertIsInstance(tools, list)
        
        # Verify all tools belong to the specified category
        for tool in tools:
            self.assertEqual(tool["category_id"], category_id)

class TestToolsSearchAPI(BaseUnitTest):
    """Unit tests for tools search API"""
    
    def test_search_without_parameters(self):
        """Test search without any parameters"""
        response = self.client.get("/api/tools/search")
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertIn("tools", result)
        self.assertIn("total", result)
        self.assertIn("page", result)
        self.assertIn("per_page", result)
        self.assertIn("total_pages", result)
        self.assertIn("has_next", result)
        self.assertIn("has_prev", result)
        
        self.assertIsInstance(result["tools"], list)
        self.assertIsInstance(result["total"], int)
    
    def test_search_with_query(self):
        """Test search with query parameter"""
        response = self.client.get("/api/tools/search?q=test")
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertIn("tools", result)
        self.assertIsInstance(result["tools"], list)
    
    def test_search_with_category_filter(self):
        """Test search with category filter"""
        if not self.test_categories:
            self.skipTest("No categories available for testing")
        
        category_id = self.test_categories[0]["id"]
        response = self.client.get(f"/api/tools/search?category_id={category_id}")
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        tools = result["tools"]
        
        # Verify all tools belong to the specified category
        for tool in tools:
            self.assertEqual(tool["category_id"], category_id)
    
    def test_search_with_pricing_filter(self):
        """Test search with pricing filter"""
        pricing_models = ["Free", "Freemium", "Paid"]
        
        for pricing_model in pricing_models:
            response = self.client.get(f"/api/tools/search?pricing_model={pricing_model}")
            
            self.assertEqual(response.status_code, 200)
            
            result = response.json()
            tools = result["tools"]
            
            # Verify all tools have the specified pricing model
            for tool in tools:
                self.assertEqual(tool["pricing_model"], pricing_model)
    
    def test_search_with_sorting(self):
        """Test search with different sorting options"""
        sort_options = ["rating", "views", "newest", "oldest", "name"]
        
        for sort_option in sort_options:
            response = self.client.get(f"/api/tools/search?sort_by={sort_option}")
            
            self.assertEqual(response.status_code, 200)
            
            result = response.json()
            self.assertIn("tools", result)
            self.assertIsInstance(result["tools"], list)
    
    def test_search_pagination(self):
        """Test search pagination"""
        # Test page 1
        response1 = self.client.get("/api/tools/search?page=1&per_page=5")
        self.assertEqual(response1.status_code, 200)
        
        result1 = response1.json()
        self.assertEqual(result1["page"], 1)
        self.assertEqual(result1["per_page"], 5)
        self.assertLessEqual(len(result1["tools"]), 5)
        
        # Test page 2 if available
        if result1["has_next"]:
            response2 = self.client.get("/api/tools/search?page=2&per_page=5")
            self.assertEqual(response2.status_code, 200)
            
            result2 = response2.json()
            self.assertEqual(result2["page"], 2)
            self.assertEqual(result2["per_page"], 5)
            
            # Verify different results
            tools1_ids = [tool["id"] for tool in result1["tools"]]
            tools2_ids = [tool["id"] for tool in result2["tools"]]
            self.assertEqual(len(set(tools1_ids) & set(tools2_ids)), 0)  # No overlap

class TestToolsAnalyticsAPI(BaseUnitTest):
    """Unit tests for tools analytics API"""
    
    def test_tools_analytics_structure(self):
        """Test tools analytics API structure"""
        response = self.client.get("/api/tools/analytics")
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        
        # Check required fields
        required_fields = [
            "trending_tools", "top_rated_tools", "most_viewed_tools",
            "newest_tools", "featured_tools", "hot_tools"
        ]
        
        for field in required_fields:
            self.assertIn(field, result)
            self.assertIsInstance(result[field], list)
    
    def test_analytics_tools_structure(self):
        """Test structure of tools in analytics"""
        response = self.client.get("/api/tools/analytics")
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        
        # Check structure of tools in each category
        for category in ["trending_tools", "top_rated_tools", "most_viewed_tools"]:
            tools = result[category]
            
            for tool in tools:
                # Check required fields
                self.assertIn("id", tool)
                self.assertIn("name", tool)
                self.assertIn("description", tool)
                self.assertIn("category_id", tool)
                self.assertIn("rating", tool)
                self.assertIn("views", tool)
                self.assertIn("created_at", tool)
                
                # Check data types
                self.assertIsInstance(tool["rating"], (int, float))
                self.assertIsInstance(tool["views"], int)

class TestBulkUploadAPI(BaseUnitTest):
    """Unit tests for bulk upload API"""
    
    def test_bulk_upload_valid_csv(self):
        """Test bulk upload with valid CSV"""
        if not self.test_categories:
            self.skipTest("No categories available for testing")
        
        # Create CSV data
        csv_data = "name,description,category_id,pricing_model,slug\n"
        csv_data += f"Test Tool 1,Test description 1,{self.test_categories[0]['id']},Free,test-tool-1\n"
        csv_data += f"Test Tool 2,Test description 2,{self.test_categories[0]['id']},Paid,test-tool-2\n"
        
        # Upload CSV
        response = self.client.post(
            "/api/tools/bulk-upload",
            files={"file": ("test.csv", csv_data.encode(), "text/csv")},
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertIn("created_count", result)
        self.assertIn("created_tools", result)
        self.assertIn("errors", result)
        
        self.assertEqual(result["created_count"], 2)
        self.assertEqual(len(result["created_tools"]), 2)
        
        # Clean up created tools
        tools_response = self.client.get("/api/tools")
        if tools_response.status_code == 200:
            all_tools = tools_response.json()
            for tool in all_tools:
                if tool["name"] in result["created_tools"]:
                    self.created_tools.append(tool["id"])
    
    def test_bulk_upload_invalid_file_type(self):
        """Test bulk upload with invalid file type"""
        # Upload non-CSV file
        response = self.client.post(
            "/api/tools/bulk-upload",
            files={"file": ("test.txt", b"not a csv file", "text/plain")},
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_bulk_upload_invalid_csv_structure(self):
        """Test bulk upload with invalid CSV structure"""
        # Create invalid CSV data
        csv_data = "invalid,headers\n"
        csv_data += "invalid,data\n"
        
        response = self.client.post(
            "/api/tools/bulk-upload",
            files={"file": ("test.csv", csv_data.encode(), "text/csv")},
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertEqual(result["created_count"], 0)
        self.assertGreater(len(result["errors"]), 0)

class TestAuthorizationUnits(BaseUnitTest):
    """Unit tests for authorization"""
    
    def test_unauthorized_access_to_tools_crud(self):
        """Test unauthorized access to tools CRUD operations"""
        tool_data = self.data_generator.generate_tool_data("auth-test")
        if self.test_categories:
            tool_data["category_id"] = self.test_categories[0]["id"]
        
        # Test without token
        response = self.client.post("/api/tools", json=tool_data)
        self.assertEqual(response.status_code, 401)
        
        # Test with invalid token
        response = self.client.post(
            "/api/tools",
            json=tool_data,
            headers={"Authorization": "Bearer invalid-token"}
        )
        self.assertEqual(response.status_code, 401)
    
    def test_user_access_to_admin_endpoints(self):
        """Test regular user access to admin endpoints"""
        try:
            user_token = self.auth.get_user_token()
            tool_data = self.data_generator.generate_tool_data("user-test")
            if self.test_categories:
                tool_data["category_id"] = self.test_categories[0]["id"]
            
            # Test user access to admin endpoint
            response = self.client.post(
                "/api/tools",
                json=tool_data,
                headers=self.auth.get_auth_headers(user_token)
            )
            
            self.assertEqual(response.status_code, 403)
        except Exception as e:
            self.skipTest(f"User authentication failed: {e}")
    
    def test_admin_access_to_tools_crud(self):
        """Test admin access to tools CRUD operations"""
        try:
            admin_token = self.auth.get_admin_token()
            tool_data = self.data_generator.generate_tool_data("admin-test")
            if self.test_categories:
                tool_data["category_id"] = self.test_categories[0]["id"]
            
            # Test admin access
            response = self.client.post(
                "/api/tools",
                json=tool_data,
                headers=self.auth.get_auth_headers(admin_token)
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Clean up
            if response.status_code == 200:
                tool_id = response.json()["id"]
                self.created_tools.append(tool_id)
                
        except Exception as e:
            self.skipTest(f"Admin authentication failed: {e}")

class TestDataValidationUnits(BaseUnitTest):
    """Unit tests for data validation"""
    
    def test_tool_name_validation(self):
        """Test tool name validation"""
        if not self.test_categories:
            self.skipTest("No categories available for testing")
        
        base_data = self.data_generator.generate_tool_data("validation-test")
        base_data["category_id"] = self.test_categories[0]["id"]
        
        # Test empty name
        invalid_data = base_data.copy()
        invalid_data["name"] = ""
        
        response = self.client.post(
            "/api/tools",
            json=invalid_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        self.assertEqual(response.status_code, 422)
        
        # Test very long name
        invalid_data = base_data.copy()
        invalid_data["name"] = "x" * 1000
        
        response = self.client.post(
            "/api/tools",
            json=invalid_data,
            headers=self.auth.get_auth_headers(self.super_admin_token)
        )
        
        # Should either pass or fail with validation error
        self.assertIn(response.status_code, [200, 422])
        
        if response.status_code == 200:
            tool_id = response.json()["id"]
            self.created_tools.append(tool_id)
    
    def test_tool_pricing_model_validation(self):
        """Test tool pricing model validation"""
        if not self.test_categories:
            self.skipTest("No categories available for testing")
        
        base_data = self.data_generator.generate_tool_data("pricing-test")
        base_data["category_id"] = self.test_categories[0]["id"]
        
        # Test valid pricing models
        valid_models = ["Free", "Freemium", "Paid"]
        for model in valid_models:
            test_data = base_data.copy()
            test_data["pricing_model"] = model
            test_data["slug"] = f"pricing-test-{model.lower()}"
            
            response = self.client.post(
                "/api/tools",
                json=test_data,
                headers=self.auth.get_auth_headers(self.super_admin_token)
            )
            
            self.assertEqual(response.status_code, 200)
            
            tool_id = response.json()["id"]
            self.created_tools.append(tool_id)
    
    def test_tool_boolean_fields_validation(self):
        """Test boolean fields validation"""
        if not self.test_categories:
            self.skipTest("No categories available for testing")
        
        base_data = self.data_generator.generate_tool_data("boolean-test")
        base_data["category_id"] = self.test_categories[0]["id"]
        
        # Test boolean fields
        boolean_tests = [
            {"is_hot": True, "is_featured": False},
            {"is_hot": False, "is_featured": True},
            {"is_hot": True, "is_featured": True},
            {"is_hot": False, "is_featured": False}
        ]
        
        for i, test_case in enumerate(boolean_tests):
            test_data = base_data.copy()
            test_data.update(test_case)
            test_data["slug"] = f"boolean-test-{i}"
            
            response = self.client.post(
                "/api/tools",
                json=test_data,
                headers=self.auth.get_auth_headers(self.super_admin_token)
            )
            
            self.assertEqual(response.status_code, 200)
            
            created_tool = response.json()
            self.created_tools.append(created_tool["id"])
            
            # Verify boolean values
            self.assertEqual(created_tool["is_hot"], test_case["is_hot"])
            self.assertEqual(created_tool["is_featured"], test_case["is_featured"])

def create_test_suite():
    """Create test suite"""
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestToolCRUDOperations,
        TestToolsSearchAPI,
        TestToolsAnalyticsAPI,
        TestBulkUploadAPI,
        TestAuthorizationUnits,
        TestDataValidationUnits
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite

def main():
    """Main function to run unit tests"""
    print("Running Super Admin Tools Unit Tests...")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    result = runner.run(suite)
    
    # Print results
    if result.wasSuccessful():
        print("\n🎉 All unit tests passed!")
        exit(0)
    else:
        print(f"\n💥 {len(result.failures)} failures, {len(result.errors)} errors")
        exit(1)

if __name__ == "__main__":
    main()