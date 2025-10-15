#!/usr/bin/env python3
"""
Test script for data collector
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

def test_data_collector():
    """Test data collector endpoints."""
    
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing Data Collector")
    print("=" * 50)
    
    # Test 1: Get collection status
    print("\n📊 Test 1: Get collection status")
    response = requests.get(f"{BASE_URL}/api/v1/data-collector/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Collection Status:")
        print(f"   Running: {data['is_running']}")
        print(f"   Symbols: {data['symbols_count']}")
        print(f"   Active tasks: {data['active_tasks']}")
        print(f"   Interval: {data['collection_interval']}s")
        print(f"   Symbols: {data['symbols'][:5]}...")  # Show first 5 symbols
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Test 2: Get latest prices
    print("\n📊 Test 2: Get latest prices")
    response = requests.get(f"{BASE_URL}/api/v1/data-collector/latest-prices", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Latest Prices:")
        for symbol, price_data in data['latest_prices'].items():
            print(f"   {symbol}: ${price_data['price']:.2f} (24h: {price_data['change_24h']}%)")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Test 3: Start collection with specific symbols
    print("\n📊 Test 3: Start collection with specific symbols")
    collection_data = {
        "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
    }
    response = requests.post(f"{BASE_URL}/api/v1/data-collector/start", json=collection_data, headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
    
    # Test 4: Monitor collection for 30 seconds
    print("\n📊 Test 4: Monitor collection")
    print("   Monitoring for 30 seconds...")
    
    for i in range(6):  # 6 iterations of 5 seconds each
        time.sleep(5)
        
        # Check collection status
        response = requests.get(f"{BASE_URL}/api/v1/data-collector/status", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"   [{i*5+5}s] Running: {data['is_running']}, Tasks: {data['active_tasks']}")
    
    # Test 5: Get latest prices again
    print("\n📊 Test 5: Get latest prices after collection")
    response = requests.get(f"{BASE_URL}/api/v1/data-collector/latest-prices", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Updated Prices:")
        for symbol, price_data in data['latest_prices'].items():
            print(f"   {symbol}: ${price_data['price']:.2f} (24h: {price_data['change_24h']}%)")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Test 6: Stop collection
    print("\n📊 Test 6: Stop collection")
    response = requests.post(f"{BASE_URL}/api/v1/data-collector/stop", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
    
    # Test 7: Final status
    print("\n📊 Test 7: Final status")
    response = requests.get(f"{BASE_URL}/api/v1/data-collector/status", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Final Status:")
        print(f"   Running: {data['is_running']}")
        print(f"   Active tasks: {data['active_tasks']}")
    else:
        print(f"❌ Failed: {response.status_code}")

def main():
    """Main test function."""
    print("🚀 Data Collector Test")
    print("=" * 50)
    
    test_data_collector()
    
    print("\n🎉 Data collector test completed!")

if __name__ == "__main__":
    main()






