#!/usr/bin/env python3
"""
MarketMindAI Review System Testing
Focus on testing the review functionality for both tools and blogs
"""

import requests
import json
import time
from datetime import datetime

# Test configuration
BACKEND_URL = "https://6ce9bd2c-20ae-4eeb-a678-dabf40be8ee0.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

# Test credentials
TEST_USERS = {
    "user": {
        "email": "user@marketmindai.com",
        "password": "password123"
    },
    "admin": {
        "email": "admin@marketmindai.com", 
        "password": "admin123"
    }
}

class ReviewTester:
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
    
    def authenticate(self):
        """Authenticate test users"""
        for user_type, credentials in TEST_USERS.items():
            try:
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
                    else:
                        self.log_test(f"Authentication - {user_type.title()}", "FAIL", 
                                    "No access token in response")
                        return False
                else:
                    self.log_test(f"Authentication - {user_type.title()}", "FAIL", 
                                f"Login failed: HTTP {response.status_code}")
                    return False
                    
            except Exception as e:
                self.log_test(f"Authentication - {user_type.title()}", "FAIL", f"Error: {str(e)}")
                return False
        return True
    
    def test_tool_reviews(self):
        """Test tool review functionality"""
        if not self.tokens.get("user"):
            self.log_test("Tool Reviews", "SKIP", "No user token available")
            return
            
        user_headers = {"Authorization": f"Bearer {self.tokens['user']}"}
        
        # Get available tools
        try:
            tools_response = self.session.get(f"{API_BASE}/tools/search?limit=5", timeout=10)
            if tools_response.status_code != 200:
                self.log_test("Tool Reviews - Setup", "FAIL", "Could not retrieve tools")
                return
            
            tools_data = tools_response.json()
            tools = tools_data.get("tools", [])
            if not tools:
                self.log_test("Tool Reviews - Setup", "FAIL", "No tools available for testing")
                return
                
            test_tool_id = tools[0]["id"]
            test_tool_name = tools[0]["name"]
            
        except Exception as e:
            self.log_test("Tool Reviews - Setup", "FAIL", f"Setup error: {str(e)}")
            return
        
        # Test creating a tool review
        try:
            review_data = {
                "rating": 5,
                "title": "Excellent tool for testing!",
                "content": "This tool works perfectly for our testing needs. Highly recommended.",
                "pros": "Easy to use, great features, reliable",
                "cons": "None found during testing"
            }
            
            response = self.session.post(
                f"{API_BASE}/tools/{test_tool_id}/reviews",
                json=review_data,
                headers=user_headers,
                timeout=10
            )
            
            if response.status_code == 201 or response.status_code == 200:
                review = response.json()
                review_id = review.get("id")
                self.log_test("Tool Review Creation", "PASS", 
                            f"Review created successfully for tool '{test_tool_name}' with ID: {review_id}")
                
                # Test getting tool reviews
                try:
                    get_response = self.session.get(
                        f"{API_BASE}/tools/{test_tool_id}/reviews",
                        timeout=10
                    )
                    
                    if get_response.status_code == 200:
                        reviews = get_response.json()
                        if isinstance(reviews, list) and len(reviews) > 0:
                            self.log_test("Tool Review Retrieval", "PASS", 
                                        f"Retrieved {len(reviews)} reviews for tool")
                        else:
                            self.log_test("Tool Review Retrieval", "FAIL", 
                                        "No reviews found after creation")
                    else:
                        self.log_test("Tool Review Retrieval", "FAIL", 
                                    f"HTTP {get_response.status_code}: {get_response.text}")
                except Exception as e:
                    self.log_test("Tool Review Retrieval", "FAIL", f"Error: {str(e)}")
                
                # Test review status
                try:
                    status_response = self.session.get(
                        f"{API_BASE}/tools/{test_tool_id}/review-status",
                        headers=user_headers,
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("has_reviewed") == True:
                            self.log_test("Tool Review Status", "PASS", 
                                        f"Status check successful: User has reviewed, Total: {status_data.get('total_reviews')}")
                        else:
                            self.log_test("Tool Review Status", "FAIL", 
                                        "Status shows user hasn't reviewed after creation")
                    else:
                        self.log_test("Tool Review Status", "FAIL", 
                                    f"HTTP {status_response.status_code}: {status_response.text}")
                except Exception as e:
                    self.log_test("Tool Review Status", "FAIL", f"Error: {str(e)}")
                
                # Clean up - delete the review
                if review_id:
                    try:
                        delete_response = self.session.delete(
                            f"{API_BASE}/tools/reviews/{review_id}",
                            headers=user_headers,
                            timeout=10
                        )
                        
                        if delete_response.status_code == 200:
                            self.log_test("Tool Review Cleanup", "PASS", "Review deleted successfully")
                        else:
                            self.log_test("Tool Review Cleanup", "FAIL", 
                                        f"HTTP {delete_response.status_code}: {delete_response.text}")
                    except Exception as e:
                        self.log_test("Tool Review Cleanup", "FAIL", f"Error: {str(e)}")
                        
            elif response.status_code == 400 and "already reviewed" in response.text.lower():
                self.log_test("Tool Review Creation", "PASS", 
                            "Duplicate review correctly prevented (user already reviewed this tool)")
            else:
                self.log_test("Tool Review Creation", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Tool Review Creation", "FAIL", f"Error: {str(e)}")
    
    def test_blog_reviews(self):
        """Test blog review functionality"""
        if not self.tokens.get("admin"):
            self.log_test("Blog Reviews", "SKIP", "No admin token available")
            return
            
        admin_headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
        
        # First create a test blog
        try:
            # Get categories for blog creation
            cat_response = self.session.get(f"{API_BASE}/categories", timeout=10)
            if cat_response.status_code != 200:
                self.log_test("Blog Reviews - Setup", "FAIL", "Could not retrieve categories")
                return
            
            categories = cat_response.json()
            if not categories:
                self.log_test("Blog Reviews - Setup", "FAIL", "No categories available")
                return
                
            category_id = categories[0]["id"]
            
            # Create test blog
            blog_data = {
                "title": f"Test Blog for Reviews - {int(time.time())}",
                "content": "This blog is created specifically for testing the review system functionality.",
                "category_id": category_id,
                "slug": f"test-blog-reviews-{int(time.time())}",
                "status": "published"
            }
            
            blog_response = self.session.post(
                f"{API_BASE}/blogs",
                json=blog_data,
                headers=admin_headers,
                timeout=10
            )
            
            if blog_response.status_code not in [200, 201]:
                self.log_test("Blog Reviews - Blog Creation", "FAIL", 
                            f"Could not create test blog: HTTP {blog_response.status_code} - {blog_response.text}")
                return
            
            blog = blog_response.json()
            blog_id = blog.get("id")
            
            if not blog_id:
                self.log_test("Blog Reviews - Blog Creation", "FAIL", "No blog ID returned")
                return
                
            self.log_test("Blog Reviews - Blog Creation", "PASS", f"Test blog created with ID: {blog_id}")
            
        except Exception as e:
            self.log_test("Blog Reviews - Blog Creation", "FAIL", f"Error: {str(e)}")
            return
        
        # Test creating a blog review
        try:
            review_data = {
                "rating": 4,
                "title": "Great blog post!",
                "content": "This blog post provides valuable insights. Well written and informative.",
                "pros": "Clear explanations, good examples",
                "cons": "Could use more detailed examples"
            }
            
            response = self.session.post(
                f"{API_BASE}/blogs/{blog_id}/reviews",
                json=review_data,
                headers=admin_headers,
                timeout=10
            )
            
            if response.status_code == 201 or response.status_code == 200:
                review = response.json()
                review_id = review.get("id")
                self.log_test("Blog Review Creation", "PASS", 
                            f"Blog review created successfully with ID: {review_id}")
                
                # Test getting blog reviews
                try:
                    get_response = self.session.get(
                        f"{API_BASE}/blogs/{blog_id}/reviews",
                        timeout=10
                    )
                    
                    if get_response.status_code == 200:
                        reviews = get_response.json()
                        if isinstance(reviews, list) and len(reviews) > 0:
                            self.log_test("Blog Review Retrieval", "PASS", 
                                        f"Retrieved {len(reviews)} reviews for blog")
                        else:
                            self.log_test("Blog Review Retrieval", "FAIL", 
                                        "No reviews found after creation")
                    else:
                        self.log_test("Blog Review Retrieval", "FAIL", 
                                    f"HTTP {get_response.status_code}: {get_response.text}")
                except Exception as e:
                    self.log_test("Blog Review Retrieval", "FAIL", f"Error: {str(e)}")
                
                # Test blog review status
                try:
                    status_response = self.session.get(
                        f"{API_BASE}/blogs/{blog_id}/review-status",
                        headers=admin_headers,
                        timeout=10
                    )
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get("has_reviewed") == True:
                            self.log_test("Blog Review Status", "PASS", 
                                        f"Status check successful: User has reviewed, Total: {status_data.get('total_reviews')}")
                        else:
                            self.log_test("Blog Review Status", "FAIL", 
                                        "Status shows user hasn't reviewed after creation")
                    else:
                        self.log_test("Blog Review Status", "FAIL", 
                                    f"HTTP {status_response.status_code}: {status_response.text}")
                except Exception as e:
                    self.log_test("Blog Review Status", "FAIL", f"Error: {str(e)}")
                
                # Clean up - delete the review
                if review_id:
                    try:
                        delete_response = self.session.delete(
                            f"{API_BASE}/blogs/reviews/{review_id}",
                            headers=admin_headers,
                            timeout=10
                        )
                        
                        if delete_response.status_code == 200:
                            self.log_test("Blog Review Cleanup", "PASS", "Blog review deleted successfully")
                        else:
                            self.log_test("Blog Review Cleanup", "FAIL", 
                                        f"HTTP {delete_response.status_code}: {delete_response.text}")
                    except Exception as e:
                        self.log_test("Blog Review Cleanup", "FAIL", f"Error: {str(e)}")
                        
            elif response.status_code == 400 and "already reviewed" in response.text.lower():
                self.log_test("Blog Review Creation", "PASS", 
                            "Duplicate review correctly prevented (user already reviewed this blog)")
            else:
                self.log_test("Blog Review Creation", "FAIL", 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Blog Review Creation", "FAIL", f"Error: {str(e)}")
        
        # Clean up - delete the test blog
        try:
            delete_blog_response = self.session.delete(
                f"{API_BASE}/blogs/{blog_id}",
                headers=admin_headers,
                timeout=10
            )
            
            if delete_blog_response.status_code == 200:
                self.log_test("Blog Cleanup", "PASS", "Test blog deleted successfully")
            else:
                self.log_test("Blog Cleanup", "FAIL", 
                            f"HTTP {delete_blog_response.status_code}: {delete_blog_response.text}")
        except Exception as e:
            self.log_test("Blog Cleanup", "FAIL", f"Error: {str(e)}")

def main():
    print("🚀 Starting MarketMindAI Review System Testing")
    print(f"📡 Testing backend at: {BACKEND_URL}")
    print("🎯 Focus: Review functionality for tools and blogs")
    print("=" * 60)
    
    tester = ReviewTester()
    
    # Authenticate users
    if not tester.authenticate():
        print("❌ Authentication failed, stopping tests")
        return 1
    
    print("\n🔍 TESTING TOOL REVIEWS:")
    print("-" * 40)
    tester.test_tool_reviews()
    
    print("\n🔍 TESTING BLOG REVIEWS:")
    print("-" * 40)
    tester.test_blog_reviews()
    
    # Print summary
    passed = sum(1 for result in tester.test_results if result["status"] == "PASS")
    failed = sum(1 for result in tester.test_results if result["status"] == "FAIL")
    skipped = sum(1 for result in tester.test_results if result["status"] == "SKIP")
    total = len(tester.test_results)
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"✅ PASSED: {passed}")
    print(f"❌ FAILED: {failed}")
    print(f"⚠️ SKIPPED: {skipped}")
    print(f"📈 TOTAL: {total}")
    
    if failed > 0:
        print(f"\n❌ FAILED TESTS:")
        for result in tester.test_results:
            if result["status"] == "FAIL":
                print(f"   • {result['test']}: {result['message']}")
    
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"\n🎯 SUCCESS RATE: {success_rate:.1f}%")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())