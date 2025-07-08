import requests
import json

BACKEND_URL = "http://localhost:8001"

def test_auth_401():
    """Test that authentication errors return 401"""
    print("Testing authentication 401 status...")
    
    # Test accessing protected endpoint without token
    response = requests.get(f"{BACKEND_URL}/api/auth/me")
    print(f"Status code: {response.status_code}")
    print(f"Expected: 401, Got: {response.status_code}")
    
    if response.status_code == 401:
        print("✅ Authentication returns 401 correctly")
        return True
    else:
        print("❌ Authentication still not returning 401")
        return False

def test_category_partial_update():
    """Test category partial update"""
    print("\nTesting category partial update...")
    
    # First login as admin
    login_data = {"email": "admin@marketmindai.com", "password": "admin123"}
    login_response = requests.post(f"{BACKEND_URL}/api/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print("❌ Failed to login as admin")
        return False
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get existing categories
    categories_response = requests.get(f"{BACKEND_URL}/api/categories")
    if categories_response.status_code != 200 or not categories_response.json():
        print("❌ No categories found")
        return False
    
    category_id = categories_response.json()[0]["id"]
    
    # Test partial update (only name)
    partial_update = {"name": "Updated CRM Name"}
    response = requests.put(f"{BACKEND_URL}/api/categories/{category_id}", 
                           json=partial_update, headers=headers)
    
    print(f"Partial update status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Category partial update working")
        return True
    else:
        print(f"❌ Category partial update failed: {response.text}")
        return False

def test_tools_comparison():
    """Test tools comparison with JSON"""
    print("\nTesting tools comparison...")
    
    # Login as user
    login_data = {"email": "user@marketmindai.com", "password": "password123"}
    login_response = requests.post(f"{BACKEND_URL}/api/auth/login", json=login_data)
    
    if login_response.status_code != 200:
        print("❌ Failed to login as user")
        return False
    
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get available tools
    tools_response = requests.get(f"{BACKEND_URL}/api/tools/search")
    if tools_response.status_code != 200 or not tools_response.json().get("tools"):
        print("❌ No tools found")
        return False
    
    tool_id = tools_response.json()["tools"][0]["id"]
    
    # Test adding tool to comparison with JSON
    comparison_data = {"tool_id": tool_id}
    response = requests.post(f"{BACKEND_URL}/api/tools/compare", 
                           json=comparison_data, headers=headers)
    
    print(f"Tools comparison status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Tools comparison working with JSON")
        return True
    else:
        print(f"❌ Tools comparison failed: {response.text}")
        return False

if __name__ == "__main__":
    print("🔧 Testing Backend Fixes...")
    
    results = []
    results.append(test_auth_401())
    results.append(test_category_partial_update())
    results.append(test_tools_comparison())
    
    print(f"\n📊 Results: {sum(results)}/3 tests passed")
    
    if all(results):
        print("🎉 All fixes are working correctly!")
    else:
        print("❌ Some fixes still need attention")
