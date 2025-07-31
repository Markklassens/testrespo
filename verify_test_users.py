#!/usr/bin/env python3
"""
Script to verify test users for testing purposes
"""

import requests
import json

BACKEND_URL = "https://f5c1f1bd-91db-440c-84c0-069afc2285da.preview.emergentagent.com"

def verify_users_via_api():
    """Try to verify users by directly calling the database update"""
    
    # First, let's try to get the verification tokens by checking if there's a way
    # Since we can't access the database directly, let's try a different approach
    
    # Try to use the superadmin to update user verification status
    test_users = [
        "superadmin@marketmindai.com",
        "admin@marketmindai.com", 
        "user@marketmindai.com"
    ]
    
    print("Attempting to verify test users...")
    
    # Since we can't directly access verification tokens, let's try to create a simple verification
    # by using a known pattern or checking if there's an admin endpoint
    
    for email in test_users:
        print(f"Checking user: {email}")
        
        # Try to login to see current status
        try:
            response = requests.post(f"{BACKEND_URL}/api/auth/login", json={
                "email": email,
                "password": "superadmin123" if "superadmin" in email else ("admin123" if "admin" in email else "password123")
            })
            
            if response.status_code == 400 and "Email not verified" in response.text:
                print(f"  - User {email} exists but not verified")
            elif response.status_code == 200:
                print(f"  - User {email} is already verified and can login")
            else:
                print(f"  - User {email} status: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"  - Error checking {email}: {e}")

if __name__ == "__main__":
    verify_users_via_api()