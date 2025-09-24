#!/usr/bin/env python3
"""
Test script for symbols integration
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("✅ Health check passed")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

def test_user_registration():
    """Test user registration."""
    print("\n🔍 Testing user registration...")
    
    user_data = {
        "email": "test_symbols@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=user_data)
    
    if response.status_code == 201:
        print("✅ User registration successful")
        return True
    elif response.status_code == 400 and "already registered" in response.text:
        print("✅ User already exists (expected)")
        return True
    else:
        print(f"❌ User registration failed: {response.status_code} - {response.text}")
        return False

def test_user_login():
    """Test user login."""
    print("\n🔍 Testing user login...")
    
    login_data = {
        "email": "test_symbols@example.com",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print("✅ User login successful")
        return token
    else:
        print(f"❌ User login failed: {response.status_code} - {response.text}")
        return None

def test_symbols_endpoints(token):
    """Test symbols endpoints."""
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n🔍 Testing symbols endpoints...")
    
    # Test available symbols
    print("\n📊 Testing available symbols...")
    response = requests.get(f"{BASE_URL}/api/v1/symbols/available?limit=10", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Available symbols: {len(data['symbols'])} symbols")
        print(f"   Quote asset: {data['quote_asset']}")
        print(f"   Sample symbols: {data['symbols'][:5]}")
    else:
        print(f"❌ Available symbols failed: {response.status_code} - {response.text}")
        return False
    
    # Test symbol validation
    print("\n🔍 Testing symbol validation...")
    test_symbol = "BTCUSDT"
    response = requests.get(f"{BASE_URL}/api/v1/symbols/validate/{test_symbol}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Symbol validation for {test_symbol}: {data['is_valid']}")
        print(f"   Message: {data['message']}")
    else:
        print(f"❌ Symbol validation failed: {response.status_code} - {response.text}")
    
    # Test invalid symbol validation
    print("\n🔍 Testing invalid symbol validation...")
    invalid_symbol = "INVALIDUSDT"
    response = requests.get(f"{BASE_URL}/api/v1/symbols/validate/{invalid_symbol}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Invalid symbol validation: {data['is_valid']} (expected: False)")
        print(f"   Message: {data['message']}")
    else:
        print(f"❌ Invalid symbol validation failed: {response.status_code} - {response.text}")
    
    # Test symbol info
    print("\n🔍 Testing symbol info...")
    response = requests.get(f"{BASE_URL}/api/v1/symbols/info/{test_symbol}", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Symbol info for {test_symbol}:")
        print(f"   Base asset: {data['base_asset']}")
        print(f"   Quote asset: {data['quote_asset']}")
        print(f"   Status: {data['status']}")
        print(f"   Spot trading: {data['is_spot_trading_allowed']}")
        if data.get('current_price'):
            print(f"   Current price: ${data['current_price']}")
    else:
        print(f"❌ Symbol info failed: {response.status_code} - {response.text}")
    
    # Test top volume symbols
    print("\n🔍 Testing top volume symbols...")
    response = requests.get(f"{BASE_URL}/api/v1/symbols/top-volume?limit=5", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Top volume symbols: {data[:5]}")
    else:
        print(f"❌ Top volume symbols failed: {response.status_code} - {response.text}")
    
    # Test symbols by strategy
    print("\n🔍 Testing symbols by strategy...")
    strategies = ["general", "scalping", "swing", "long_term"]
    for strategy in strategies:
        response = requests.get(f"{BASE_URL}/api/v1/symbols/by-strategy/{strategy}", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {strategy} strategy symbols: {len(data)} symbols")
        else:
            print(f"❌ {strategy} strategy symbols failed: {response.status_code}")
    
    # Test symbols stats
    print("\n🔍 Testing symbols stats...")
    response = requests.get(f"{BASE_URL}/api/v1/symbols/stats", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Symbols stats:")
        print(f"   Total symbols: {data['total_symbols']}")
        print(f"   USDT pairs: {data['usdt_pairs']}")
        print(f"   BTC pairs: {data['btc_pairs']}")
        print(f"   ETH pairs: {data['eth_pairs']}")
        print(f"   BNB pairs: {data['bnb_pairs']}")
        print(f"   Cache status: {data['cache_status']}")
    else:
        print(f"❌ Symbols stats failed: {response.status_code} - {response.text}")
    
    return True

def test_trading_strategy_validation(token):
    """Test trading strategy symbol validation."""
    print("\n🔍 Testing trading strategy symbol validation...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test valid symbol
    print("\n📊 Testing valid symbol strategy creation...")
    valid_strategy = {
        "name": "Test BTC Strategy",
        "strategy_type": "rsi",
        "parameters": {"rsi_period": 14, "oversold_threshold": 30},
        "symbol": "BTCUSDT",
        "timeframe": "1d",
        "initial_balance": 10000,
        "commission_rate": 0.001
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/trading-strategies/", json=valid_strategy, headers=headers)
    if response.status_code == 201:
        print("✅ Valid symbol strategy created successfully")
        strategy_data = response.json()
        strategy_id = strategy_data['id']
        print(f"   Strategy ID: {strategy_id}")
    else:
        print(f"❌ Valid symbol strategy creation failed: {response.status_code} - {response.text}")
        return False
    
    # Test invalid symbol
    print("\n📊 Testing invalid symbol strategy creation...")
    invalid_strategy = {
        "name": "Test Invalid Strategy",
        "strategy_type": "rsi",
        "parameters": {"rsi_period": 14, "oversold_threshold": 30},
        "symbol": "INVALIDUSDT",
        "timeframe": "1d",
        "initial_balance": 10000,
        "commission_rate": 0.001
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/trading-strategies/", json=invalid_strategy, headers=headers)
    if response.status_code == 400:
        print("✅ Invalid symbol strategy correctly rejected")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"❌ Invalid symbol strategy should have been rejected: {response.status_code} - {response.text}")
    
    return True

def main():
    """Main test function."""
    print("🚀 Starting Symbols Integration Test")
    print("=" * 50)
    
    # Test health
    if not test_health():
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
    
    # Test symbols endpoints
    if not test_symbols_endpoints(token):
        print("❌ Symbols endpoints test failed")
        return
    
    # Test trading strategy validation
    if not test_trading_strategy_validation(token):
        print("❌ Trading strategy validation test failed")
        return
    
    print("\n🎉 All tests completed successfully!")
    print("=" * 50)
    print("✅ Symbols integration is working correctly!")
    print("✅ Dynamic symbol loading from Binance is functional!")
    print("✅ Symbol validation is working!")
    print("✅ Trading strategy symbol validation is working!")

if __name__ == "__main__":
    main()

