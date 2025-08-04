#!/usr/bin/env python3
"""
MarketMindAI Bulk Upload Testing Suite
Focused testing of Super Admin bulk upload functionality
"""

import requests
import json
import io
import csv
from datetime import datetime

# Test configuration
BACKEND_URL = "https://93364546-03cb-4ae8-a6a0-909ce7700a55.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class BulkUploadTester:
    def __init__(self):
        self.session = requests.Session()
        self.superadmin_token = None
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
    
    def authenticate_superadmin(self):
        """Authenticate as superadmin"""
        try:
            response = self.session.post(
                f"{API_BASE}/auth/login",
                json={
                    "email": "superadmin@marketmindai.com",
                    "password": "superadmin123"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.superadmin_token = data["access_token"]
                self.log_test("SuperAdmin Authentication", "PASS", "Successfully authenticated as SuperAdmin")
                return True
            else:
                self.log_test("SuperAdmin Authentication", "FAIL", f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("SuperAdmin Authentication", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_csv_template_download(self):
        """Test CSV template download endpoint"""
        if not self.superadmin_token:
            self.log_test("CSV Template Download", "SKIP", "No superadmin token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.superadmin_token}"}
        
        try:
            response = self.session.get(
                f"{API_BASE}/superadmin/tools/sample-csv",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                csv_content = response.text
                
                # Check if response is CSV format
                if response.headers.get("content-type") == "text/csv":
                    # Check if CSV contains category_name field (not category_id)
                    if "category_name" in csv_content:
                        # Check if available categories are listed at the end
                        if "# Available Categories" in csv_content:
                            self.log_test("CSV Template Download", "PASS", 
                                        "CSV template downloaded successfully with category names and available categories list")
                            
                            # Extract and show available categories
                            lines = csv_content.split('\n')
                            categories = [line.replace('# - ', '') for line in lines if line.startswith('# - ')]
                            if categories:
                                self.log_test("CSV Template Categories", "PASS", 
                                            f"Found {len(categories)} available categories: {', '.join(categories)}")
                            
                            return True
                        else:
                            self.log_test("CSV Template Download", "FAIL", 
                                        "CSV template missing available categories list")
                    else:
                        self.log_test("CSV Template Download", "FAIL", 
                                    "CSV template missing category_name field")
                else:
                    self.log_test("CSV Template Download", "FAIL", 
                                f"Wrong content type: {response.headers.get('content-type')}")
            else:
                self.log_test("CSV Template Download", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("CSV Template Download", "FAIL", f"Error: {str(e)}")
            
        return False
    
    def get_available_categories(self):
        """Get available categories for testing"""
        try:
            response = self.session.get(f"{API_BASE}/categories", timeout=10)
            if response.status_code == 200:
                categories = response.json()
                if categories:
                    return categories
            return []
        except:
            return []
    
    def test_bulk_upload_with_category_names(self):
        """Test bulk upload using category names"""
        if not self.superadmin_token:
            self.log_test("Bulk Upload - Category Names", "SKIP", "No superadmin token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.superadmin_token}"}
        
        # Get available categories
        categories = self.get_available_categories()
        if not categories:
            self.log_test("Bulk Upload - Category Names", "SKIP", "No categories available for testing")
            return False
            
        test_category_name = categories[0]["name"]
        
        try:
            # Create CSV content with category name
            csv_content = f"""name,description,website_url,pricing_model,category_name,features,integrations
Test Tool Category Name,Test tool uploaded with category name,https://testtool-name.com,Freemium,{test_category_name},"Task management,Collaboration","Slack,Google Drive"
Test Tool 2,Another test tool with category name,https://testtool2.com,Paid,{test_category_name},"Project tracking,Reporting","Zoom,Dropbox"
"""
            
            # Create file-like object
            csv_file = io.BytesIO(csv_content.encode('utf-8'))
            
            files = {"file": ("test_category_name.csv", csv_file, "text/csv")}
            
            response = self.session.post(
                f"{API_BASE}/superadmin/tools/bulk-upload",
                files=files,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                total_processed = result.get("total_processed", 0)
                total_errors = result.get("total_errors", 0)
                
                if total_processed > 0 and total_errors == 0:
                    self.log_test("Bulk Upload - Category Names", "PASS", 
                                f"Successfully uploaded {total_processed} tools using category name '{test_category_name}'")
                    return True
                else:
                    self.log_test("Bulk Upload - Category Names", "FAIL", 
                                f"Upload had errors: {result.get('errors', [])}")
            else:
                self.log_test("Bulk Upload - Category Names", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Bulk Upload - Category Names", "FAIL", f"Error: {str(e)}")
            
        return False
    
    def test_bulk_upload_with_category_ids(self):
        """Test bulk upload using category IDs (backward compatibility)"""
        if not self.superadmin_token:
            self.log_test("Bulk Upload - Category IDs", "SKIP", "No superadmin token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.superadmin_token}"}
        
        # Get available categories
        categories = self.get_available_categories()
        if not categories:
            self.log_test("Bulk Upload - Category IDs", "SKIP", "No categories available for testing")
            return False
            
        test_category_id = categories[0]["id"]
        
        try:
            # Create CSV content with category ID
            csv_content = f"""name,description,website_url,pricing_model,category_id,features,integrations
Test Tool Category ID,Test tool uploaded with category ID,https://testtool-id.com,Paid,{test_category_id},"Project management,Analytics","Zoom,Dropbox"
"""
            
            # Create file-like object
            csv_file = io.BytesIO(csv_content.encode('utf-8'))
            
            files = {"file": ("test_category_id.csv", csv_file, "text/csv")}
            
            response = self.session.post(
                f"{API_BASE}/superadmin/tools/bulk-upload",
                files=files,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                total_processed = result.get("total_processed", 0)
                total_errors = result.get("total_errors", 0)
                
                if total_processed > 0 and total_errors == 0:
                    self.log_test("Bulk Upload - Category IDs", "PASS", 
                                f"Successfully uploaded {total_processed} tools using category ID '{test_category_id}'")
                    return True
                else:
                    self.log_test("Bulk Upload - Category IDs", "FAIL", 
                                f"Upload had errors: {result.get('errors', [])}")
            else:
                self.log_test("Bulk Upload - Category IDs", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Bulk Upload - Category IDs", "FAIL", f"Error: {str(e)}")
            
        return False
    
    def test_bulk_upload_error_handling(self):
        """Test error handling for invalid data"""
        if not self.superadmin_token:
            self.log_test("Bulk Upload - Error Handling", "SKIP", "No superadmin token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.superadmin_token}"}
        
        # Test 1: Invalid category name
        try:
            csv_content_invalid = """name,description,website_url,pricing_model,category_name,features,integrations
Test Tool Invalid,Test tool with invalid category,https://testtool-invalid.com,Free,NonExistentCategory,"Testing,Validation","API,Database"
"""
            
            csv_file = io.BytesIO(csv_content_invalid.encode('utf-8'))
            files = {"file": ("test_invalid.csv", csv_file, "text/csv")}
            
            response = self.session.post(
                f"{API_BASE}/superadmin/tools/bulk-upload",
                files=files,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("total_errors", 0) > 0:
                    error_messages = str(result.get("errors", []))
                    if "Category name not found" in error_messages or "not found" in error_messages:
                        self.log_test("Bulk Upload - Invalid Category", "PASS", 
                                    "Correctly rejected upload with invalid category name")
                    else:
                        self.log_test("Bulk Upload - Invalid Category", "FAIL", 
                                    f"Wrong error message: {error_messages}")
                else:
                    self.log_test("Bulk Upload - Invalid Category", "FAIL", 
                                "Should have rejected invalid category name")
            else:
                self.log_test("Bulk Upload - Invalid Category", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Bulk Upload - Invalid Category", "FAIL", f"Error: {str(e)}")
        
        # Test 2: Missing required fields
        try:
            csv_content_missing = """name,description,pricing_model,category_name
Test Tool Missing,Missing website URL,Free,Project Management
"""
            
            csv_file = io.BytesIO(csv_content_missing.encode('utf-8'))
            files = {"file": ("test_missing.csv", csv_file, "text/csv")}
            
            response = self.session.post(
                f"{API_BASE}/superadmin/tools/bulk-upload",
                files=files,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("total_errors", 0) > 0:
                    error_messages = str(result.get("errors", []))
                    if "Missing required fields" in error_messages or "website_url" in error_messages:
                        self.log_test("Bulk Upload - Missing Fields", "PASS", 
                                    "Correctly rejected upload with missing required fields")
                    else:
                        self.log_test("Bulk Upload - Missing Fields", "FAIL", 
                                    f"Wrong error message: {error_messages}")
                else:
                    self.log_test("Bulk Upload - Missing Fields", "FAIL", 
                                "Should have rejected missing required fields")
            else:
                self.log_test("Bulk Upload - Missing Fields", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Bulk Upload - Missing Fields", "FAIL", f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all bulk upload tests"""
        print("🚀 Starting MarketMindAI Bulk Upload Testing Suite")
        print("📡 Testing backend at:", BACKEND_URL)
        print("🎯 Focus: Super Admin bulk upload functionality")
        print("=" * 60)
        
        # Authenticate
        if not self.authenticate_superadmin():
            print("❌ Cannot proceed without SuperAdmin authentication")
            return
        
        # Run tests
        self.test_csv_template_download()
        self.test_bulk_upload_with_category_names()
        self.test_bulk_upload_with_category_ids()
        self.test_bulk_upload_error_handling()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        skipped = len([r for r in self.test_results if r["status"] == "SKIP"])
        total = len(self.test_results)
        
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"⚠️ SKIPPED: {skipped}")
        print(f"📈 TOTAL: {total}")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   • {result['test']}: {result['message']}")
        
        success_rate = (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
        print(f"\n🎯 SUCCESS RATE: {success_rate:.1f}%")

if __name__ == "__main__":
    tester = BulkUploadTester()
    tester.run_all_tests()