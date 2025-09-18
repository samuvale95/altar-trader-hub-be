#!/usr/bin/env python3
"""
Test script for Trading Strategies API
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

# Test data
test_user = {
    "email": "test2@example.com",
    "password": "testpassword123",
    "first_name": "Test",
    "last_name": "User"
}

def test_user_registration():
    """Test user registration."""
    print("Testing user registration...")
    
    response = requests.post(f"{API_BASE}/auth/register", json=test_user)
    
    if response.status_code == 201:
        print("✅ User registration: SUCCESS")
        return True
    elif response.status_code == 400 and "already registered" in response.text:
        print("✅ User registration: ALREADY EXISTS (OK)")
        return True
    else:
        print(f"❌ User registration: FAILED - {response.status_code} - {response.text}")
        return False

def test_user_login():
    """Test user login."""
    print("Testing user login...")
    
    login_data = {
        "email": test_user["email"],
        "password": test_user["password"]
    }
    
    response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print("✅ User login: SUCCESS")
        return token
    else:
        print(f"❌ User login: FAILED - {response.status_code} - {response.text}")
        return None

def test_available_strategies(token):
    """Test getting available strategies."""
    print("Testing available strategies...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/trading-strategies/available", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        strategies = data.get("strategies", [])
        print(f"✅ Available strategies: SUCCESS - {len(strategies)} strategies found")
        
        for strategy in strategies[:3]:  # Show first 3
            print(f"   - {strategy['name']} ({strategy['type']})")
        
        return True
    else:
        print(f"❌ Available strategies: FAILED - {response.status_code} - {response.text}")
        return False

def test_create_strategy(token):
    """Test creating a trading strategy."""
    print("Testing create strategy...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    strategy_data = {
        "name": "Test RSI Strategy",
        "description": "Test RSI strategy for BTCUSDT",
        "strategy_type": "rsi",
        "parameters": {
            "rsi_period": 14,
            "oversold_threshold": 30,
            "overbought_threshold": 70
        },
        "symbol": "BTCUSDT",
        "timeframe": "1d",
        "initial_balance": 10000.0,
        "commission_rate": 0.001,
        "auto_start": False
    }
    
    response = requests.post(f"{API_BASE}/trading-strategies/", json=strategy_data, headers=headers)
    
    if response.status_code == 201:
        data = response.json()
        strategy_id = data.get("id")
        print(f"✅ Create strategy: SUCCESS - Strategy ID: {strategy_id}")
        return strategy_id
    else:
        print(f"❌ Create strategy: FAILED - {response.status_code} - {response.text}")
        return None

def test_get_strategies(token):
    """Test getting user strategies."""
    print("Testing get strategies...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/trading-strategies/", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        strategies = data.get("strategies", [])
        total = data.get("total", 0)
        print(f"✅ Get strategies: SUCCESS - {len(strategies)} strategies (total: {total})")
        
        for strategy in strategies:
            print(f"   - {strategy['name']} ({strategy['strategy_type']}) - Status: {strategy['status']}")
        
        return strategies
    else:
        print(f"❌ Get strategies: FAILED - {response.status_code} - {response.text}")
        return []

def test_control_strategy(token, strategy_id):
    """Test controlling a strategy."""
    print("Testing strategy control...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test start strategy
    control_data = {"action": "start"}
    response = requests.post(f"{API_BASE}/trading-strategies/{strategy_id}/control", json=control_data, headers=headers)
    
    if response.status_code == 200:
        print("✅ Start strategy: SUCCESS")
    else:
        print(f"❌ Start strategy: FAILED - {response.status_code} - {response.text}")
    
    # Wait a bit
    time.sleep(2)
    
    # Test stop strategy
    control_data = {"action": "stop"}
    response = requests.post(f"{API_BASE}/trading-strategies/{strategy_id}/control", json=control_data, headers=headers)
    
    if response.status_code == 200:
        print("✅ Stop strategy: SUCCESS")
    else:
        print(f"❌ Stop strategy: FAILED - {response.status_code} - {response.text}")

def test_run_backtest(token, strategy_id):
    """Test running a backtest."""
    print("Testing run backtest...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    backtest_data = {
        "strategy_id": strategy_id,
        "name": "Test Backtest",
        "description": "Test backtest for RSI strategy",
        "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
        "end_date": datetime.now().isoformat(),
        "symbol": "BTCUSDT",
        "timeframe": "1d"
    }
    
    response = requests.post(f"{API_BASE}/trading-strategies/{strategy_id}/backtest", json=backtest_data, headers=headers)
    
    if response.status_code == 201:
        data = response.json()
        backtest_id = data.get("id")
        print(f"✅ Run backtest: SUCCESS - Backtest ID: {backtest_id}")
        return backtest_id
    else:
        print(f"❌ Run backtest: FAILED - {response.status_code} - {response.text}")
        return None

def test_get_backtests(token, strategy_id):
    """Test getting backtest results."""
    print("Testing get backtests...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/trading-strategies/{strategy_id}/backtests", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        backtests = data.get("backtests", [])
        total = data.get("total", 0)
        print(f"✅ Get backtests: SUCCESS - {len(backtests)} backtests (total: {total})")
        
        for backtest in backtests:
            total_return = float(backtest.get('total_return', 0)) * 100
            print(f"   - {backtest['name']} - Status: {backtest['status']} - Return: {total_return:.2f}%")
        
        return backtests
    else:
        print(f"❌ Get backtests: FAILED - {response.status_code} - {response.text}")
        return []

def test_dashboard_overview(token):
    """Test dashboard overview."""
    print("Testing dashboard overview...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/trading-monitor/dashboard/overview", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        stats = data.get("statistics", {})
        print(f"✅ Dashboard overview: SUCCESS")
        print(f"   - Total strategies: {stats.get('total_strategies', 0)}")
        print(f"   - Active strategies: {stats.get('active_strategies', 0)}")
        print(f"   - Total backtests: {stats.get('total_backtests', 0)}")
        print(f"   - Total trades: {stats.get('total_trades', 0)}")
        return True
    else:
        print(f"❌ Dashboard overview: FAILED - {response.status_code} - {response.text}")
        return False

def test_market_data(token):
    """Test market data endpoint."""
    print("Testing market data...")
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/trading-monitor/market/data/BTCUSDT?timeframe=1d&limit=10", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        count = data.get("count", 0)
        print(f"✅ Market data: SUCCESS - {count} data points")
        return True
    else:
        print(f"❌ Market data: FAILED - {response.status_code} - {response.text}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("TRADING STRATEGIES API TEST SUITE")
    print("=" * 60)
    
    # Test user registration and login
    if not test_user_registration():
        print("Cannot continue without user registration")
        return
    
    token = test_user_login()
    if not token:
        print("Cannot continue without authentication")
        return
    
    print("\n" + "=" * 40)
    
    # Test available strategies
    test_available_strategies(token)
    
    # Test create strategy
    strategy_id = test_create_strategy(token)
    if not strategy_id:
        print("Cannot continue without strategy creation")
        return
    
    print("\n" + "=" * 40)
    
    # Test get strategies
    strategies = test_get_strategies(token)
    
    # Test control strategy
    test_control_strategy(token, strategy_id)
    
    print("\n" + "=" * 40)
    
    # Test run backtest
    backtest_id = test_run_backtest(token, strategy_id)
    
    # Test get backtests
    backtests = test_get_backtests(token, strategy_id)
    
    print("\n" + "=" * 40)
    
    # Test dashboard and monitoring
    test_dashboard_overview(token)
    test_market_data(token)
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()
