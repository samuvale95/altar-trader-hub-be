#!/usr/bin/env python3
"""
Test script for strategy control
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def get_auth_token():
    """Get authentication token."""
    login_data = {
        "email": "test_symbols@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def test_strategy_control():
    """Test strategy control endpoints."""
    
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing Strategy Control")
    print("=" * 50)
    
    # Test 1: Get strategies status
    print("\n📊 Test 1: Get strategies status")
    response = requests.get(f"{BASE_URL}/api/v1/strategy-control/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Strategies Status:")
        print(f"   Total strategies: {data['total_strategies']}")
        print(f"   Active strategies: {data['active_strategies']}")
        for strategy in data['strategies']:
            print(f"   Strategy {strategy['id']}: {strategy['name']}")
            print(f"     Type: {strategy['strategy_type']}")
            print(f"     Status: {strategy['status']}")
            print(f"     Active: {strategy['is_active']}")
            print(f"     Started: {strategy['started_at']}")
            print(f"     Last run: {strategy['last_run_at']}")
            print(f"     Trades: {strategy['total_trades']}")
            print(f"     Balance: {strategy['current_balance']}")
            print()
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Test 2: Start strategy 6
    print("\n📊 Test 2: Start strategy 6")
    response = requests.post(f"{BASE_URL}/api/v1/strategy-control/6/start", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
    
    # Test 3: Check status again
    print("\n📊 Test 3: Check status after start")
    response = requests.get(f"{BASE_URL}/api/v1/strategy-control/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Active strategies: {data['active_strategies']}")
        for strategy in data['strategies']:
            if strategy['is_active']:
                print(f"   Active: {strategy['name']} - {strategy['status']}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Test 4: Stop strategy 6
    print("\n📊 Test 4: Stop strategy 6")
    response = requests.post(f"{BASE_URL}/api/v1/strategy-control/6/stop", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
    
    # Test 5: Check final status
    print("\n📊 Test 5: Final status check")
    response = requests.get(f"{BASE_URL}/api/v1/strategy-control/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Final active strategies: {data['active_strategies']}")
    else:
        print(f"❌ Failed: {response.status_code}")

def main():
    """Main test function."""
    print("🚀 Strategy Control Test")
    print("=" * 50)
    
    test_strategy_control()
    
    print("\n🎉 Strategy control test completed!")

if __name__ == "__main__":
    main()
