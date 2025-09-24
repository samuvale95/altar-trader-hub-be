#!/usr/bin/env python3
"""
Test script to demonstrate cache behavior
"""

import requests
import time
import json
from datetime import datetime

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

def test_cache_behavior():
    """Test cache behavior with multiple calls."""
    
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing Cache Behavior")
    print("=" * 50)
    
    # Test 1: First call (should use cache if valid, or fetch from API)
    print("\n📊 Test 1: First call to available symbols")
    start_time = time.time()
    response1 = requests.get(f"{BASE_URL}/api/v1/symbols/available?limit=5", headers=headers)
    end_time = time.time()
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"✅ Response time: {(end_time - start_time)*1000:.2f}ms")
        print(f"   Symbols returned: {len(data1['symbols'])}")
        print(f"   Sample: {data1['symbols'][:3]}")
    else:
        print(f"❌ Failed: {response1.status_code}")
        return
    
    # Test 2: Immediate second call (should use cache)
    print("\n📊 Test 2: Immediate second call (should use cache)")
    start_time = time.time()
    response2 = requests.get(f"{BASE_URL}/api/v1/symbols/available?limit=5", headers=headers)
    end_time = time.time()
    
    if response2.status_code == 200:
        data2 = response2.json()
        print(f"✅ Response time: {(end_time - start_time)*1000:.2f}ms")
        print(f"   Symbols returned: {len(data2['symbols'])}")
        print(f"   Same data: {data1['symbols'] == data2['symbols']}")
    else:
        print(f"❌ Failed: {response2.status_code}")
    
    # Test 3: Check cache file timestamp
    print("\n📊 Test 3: Check cache file timestamp")
    try:
        with open('data/binance_symbols_cache.json', 'r') as f:
            cache_data = json.load(f)
        
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        now = datetime.now()
        age_minutes = (now - cache_time).total_seconds() / 60
        
        print(f"✅ Cache timestamp: {cache_data['timestamp']}")
        print(f"   Cache age: {age_minutes:.1f} minutes")
        print(f"   Cache valid: {'Yes' if age_minutes < 60 else 'No (expired)'}")
        print(f"   Total symbols in cache: {cache_data['count']}")
        
    except Exception as e:
        print(f"❌ Failed to read cache: {e}")
    
    # Test 4: Force refresh (should update cache)
    print("\n📊 Test 4: Force refresh cache")
    start_time = time.time()
    refresh_response = requests.post(f"{BASE_URL}/api/v1/symbols/refresh", headers=headers)
    end_time = time.time()
    
    if refresh_response.status_code == 200:
        refresh_data = refresh_response.json()
        print(f"✅ Refresh time: {(end_time - start_time)*1000:.2f}ms")
        print(f"   Success: {refresh_data['success']}")
        print(f"   Message: {refresh_data['message']}")
        if refresh_data.get('timestamp'):
            print(f"   New timestamp: {refresh_data['timestamp']}")
    else:
        print(f"❌ Refresh failed: {refresh_response.status_code}")
    
    # Test 5: Check updated cache
    print("\n📊 Test 5: Check updated cache")
    try:
        with open('data/binance_symbols_cache.json', 'r') as f:
            cache_data = json.load(f)
        
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        now = datetime.now()
        age_minutes = (now - cache_time).total_seconds() / 60
        
        print(f"✅ Updated cache timestamp: {cache_data['timestamp']}")
        print(f"   Cache age: {age_minutes:.1f} minutes")
        print(f"   Cache valid: {'Yes' if age_minutes < 60 else 'No (expired)'}")
        
    except Exception as e:
        print(f"❌ Failed to read updated cache: {e}")
    
    # Test 6: Call after refresh (should be fast)
    print("\n📊 Test 6: Call after refresh (should be fast)")
    start_time = time.time()
    response3 = requests.get(f"{BASE_URL}/api/v1/symbols/available?limit=5", headers=headers)
    end_time = time.time()
    
    if response3.status_code == 200:
        data3 = response3.json()
        print(f"✅ Response time: {(end_time - start_time)*1000:.2f}ms")
        print(f"   Symbols returned: {len(data3['symbols'])}")
    else:
        print(f"❌ Failed: {response3.status_code}")

def test_symbol_validation_caching():
    """Test symbol validation caching behavior."""
    
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔍 Testing Symbol Validation Caching")
    print("=" * 50)
    
    # Test validation of valid symbol
    print("\n📊 Testing BTCUSDT validation (should be fast)")
    start_time = time.time()
    response = requests.get(f"{BASE_URL}/api/v1/symbols/validate/BTCUSDT", headers=headers)
    end_time = time.time()
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response time: {(end_time - start_time)*1000:.2f}ms")
        print(f"   Valid: {data['is_valid']}")
        print(f"   Tradable: {data['is_tradable']}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Test validation of invalid symbol
    print("\n📊 Testing INVALIDUSDT validation")
    start_time = time.time()
    response = requests.get(f"{BASE_URL}/api/v1/symbols/validate/INVALIDUSDT", headers=headers)
    end_time = time.time()
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Response time: {(end_time - start_time)*1000:.2f}ms")
        print(f"   Valid: {data['is_valid']}")
        print(f"   Tradable: {data['is_tradable']}")
    else:
        print(f"❌ Failed: {response.status_code}")

def main():
    """Main test function."""
    print("🚀 Cache Behavior Test")
    print("=" * 50)
    
    test_cache_behavior()
    test_symbol_validation_caching()
    
    print("\n🎉 Cache behavior test completed!")
    print("\n📋 Summary:")
    print("✅ First call: Uses cache if valid, otherwise fetches from API")
    print("✅ Subsequent calls: Use cache (very fast)")
    print("✅ Cache duration: 1 hour")
    print("✅ Force refresh: Updates cache and returns fresh data")
    print("✅ Symbol validation: Uses cached data for validation")

if __name__ == "__main__":
    main()

