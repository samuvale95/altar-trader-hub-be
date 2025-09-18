#!/usr/bin/env python3
"""
Test script to verify the API is working correctly.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Health check passed: {data['status']}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

def test_user_registration():
    """Test user registration."""
    print("\nTesting user registration...")
    user_data = {
        "email": "test@example.com",
        "password": "test12345",
        "full_name": "Test User"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/register",
        json=user_data
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ User registration passed: {data['email']}")
        return True
    elif response.status_code == 400 and "already registered" in response.text:
        print("✅ User already registered (expected)")
        return True
    else:
        print(f"❌ User registration failed: {response.status_code} - {response.text}")
        return False

def test_user_login():
    """Test user login."""
    print("\nTesting user login...")
    login_data = {
        "email": "test@example.com",
        "password": "test12345"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json=login_data
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ User login passed: {data['token_type']}")
        return data['access_token']
    else:
        print(f"❌ User login failed: {response.status_code} - {response.text}")
        return None

def test_protected_endpoint(token):
    """Test a protected endpoint."""
    print("\nTesting protected endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/api/v1/auth/me",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Protected endpoint passed: {data['email']}")
        return True
    else:
        print(f"❌ Protected endpoint failed: {response.status_code} - {response.text}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting API tests...")
    
    # Test health check
    if not test_health_check():
        print("❌ Health check failed, stopping tests")
        return
    
    # Test user registration
    if not test_user_registration():
        print("❌ User registration failed, stopping tests")
        return
    
    # Test user login
    token = test_user_login()
    if not token:
        print("❌ User login failed, stopping tests")
        return
    
    # Test protected endpoint
    test_protected_endpoint(token)
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    main()
