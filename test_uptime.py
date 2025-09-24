#!/usr/bin/env python3
"""
Test script for uptime monitoring
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

def test_uptime_endpoints():
    """Test uptime monitoring endpoints."""
    
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing Uptime Monitoring")
    print("=" * 50)
    
    # Test 1: Simple uptime
    print("\n📊 Test 1: Simple uptime")
    response = requests.get(f"{BASE_URL}/api/v1/system/uptime", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Uptime: {data['uptime_human']}")
        print(f"   Start time: {data['start_time']}")
        print(f"   Current time: {data['current_time']}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Test 2: System status
    print("\n📊 Test 2: System status")
    response = requests.get(f"{BASE_URL}/api/v1/system/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ System Status:")
        print(f"   Status: {data['status']}")
        print(f"   Uptime: {data['uptime_human']}")
        print(f"   Start time: {data['start_time']}")
        print(f"   Version: {data['version']}")
        print(f"   Environment: {data['environment']}")
        print(f"   Memory usage: {data['memory_usage_mb']} MB")
        print(f"   CPU usage: {data['cpu_usage_percent']}%")
        print(f"   Active strategies: {data['active_strategies']}")
        print(f"   Total strategies: {data['total_strategies']}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Test 3: Strategies uptime
    print("\n📊 Test 3: Strategies uptime")
    response = requests.get(f"{BASE_URL}/api/v1/system/strategies/uptime", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Strategies Uptime:")
        for strategy in data:
            print(f"   Strategy {strategy['strategy_id']}: {strategy['strategy_name']}")
            print(f"     Status: {strategy['status']}")
            print(f"     Active: {strategy['is_active']}")
            print(f"     Uptime: {strategy['uptime_human']}")
            print(f"     Started: {strategy['started_at']}")
            print(f"     Last run: {strategy['last_run_at']}")
            print(f"     Total trades: {strategy['total_trades']}")
            print(f"     Balance: {strategy['current_balance']}")
            print()
    else:
        print(f"❌ Failed: {response.status_code}")

def main():
    """Main test function."""
    print("🚀 Uptime Monitoring Test")
    print("=" * 50)
    
    test_uptime_endpoints()
    
    print("\n🎉 Uptime monitoring test completed!")

if __name__ == "__main__":
    main()

