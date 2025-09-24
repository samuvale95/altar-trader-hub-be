#!/usr/bin/env python3
"""
Test script for strategy execution
"""

import requests
import json
import time

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

def test_strategy_execution():
    """Test strategy execution."""
    
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing Strategy Execution")
    print("=" * 50)
    
    # Test 1: Start strategy
    print("\n📊 Test 1: Start strategy 6")
    response = requests.post(f"{BASE_URL}/api/v1/strategy-control/6/start", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return
    
    # Test 2: Monitor strategy for 30 seconds
    print("\n📊 Test 2: Monitor strategy execution")
    print("   Monitoring for 30 seconds...")
    
    for i in range(6):  # 6 iterations of 5 seconds each
        time.sleep(5)
        
        # Check strategy status
        response = requests.get(f"{BASE_URL}/api/v1/strategy-control/status", headers=headers)
        if response.status_code == 200:
            data = response.json()
            for strategy in data['strategies']:
                if strategy['id'] == 6:
                    print(f"   [{i*5+5}s] Strategy {strategy['name']}:")
                    print(f"     Status: {strategy['status']}")
                    print(f"     Active: {strategy['is_active']}")
                    print(f"     Last run: {strategy['last_run_at']}")
                    print(f"     Trades: {strategy['total_trades']}")
                    print(f"     Balance: {strategy['current_balance']}")
                    print()
                    break
    
    # Test 3: Stop strategy
    print("\n📊 Test 3: Stop strategy")
    response = requests.post(f"{BASE_URL}/api/v1/strategy-control/6/stop", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
    
    # Test 4: Final status
    print("\n📊 Test 4: Final status")
    response = requests.get(f"{BASE_URL}/api/v1/strategy-control/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        for strategy in data['strategies']:
            if strategy['id'] == 6:
                print(f"✅ Final Status:")
                print(f"   Status: {strategy['status']}")
                print(f"   Active: {strategy['is_active']}")
                print(f"   Total trades: {strategy['total_trades']}")
                print(f"   Final balance: {strategy['current_balance']}")
                break

def main():
    """Main test function."""
    print("🚀 Strategy Execution Test")
    print("=" * 50)
    
    test_strategy_execution()
    
    print("\n🎉 Strategy execution test completed!")

if __name__ == "__main__":
    main()

