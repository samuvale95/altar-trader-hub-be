#!/usr/bin/env python3
"""
Test script for Charts API endpoints.
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test credentials (you'll need to register a user first)
TEST_USER = {
    "email": "test@example.com",
    "password": "testpassword123"
}

class ChartsAPITester:
    """Test class for Charts API endpoints."""
    
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.test_symbol = "BTCUSDT"
        self.test_timeframe = "1h"
    
    def authenticate(self):
        """Authenticate and get access token."""
        print("🔐 Authenticating...")
        
        # Try to login first
        login_response = self.session.post(
            f"{API_BASE}/auth/login",
            json=TEST_USER
        )
        
        if login_response.status_code == 200:
            self.auth_token = login_response.json()["access_token"]
            print("✅ Login successful")
        else:
            # Try to register if login fails
            print("📝 Registering new user...")
            register_response = self.session.post(
                f"{API_BASE}/auth/register",
                json=TEST_USER
            )
            
            if register_response.status_code == 201:
                print("✅ Registration successful")
                # Now login
                login_response = self.session.post(
                    f"{API_BASE}/auth/login",
                    json=TEST_USER
                )
                if login_response.status_code == 200:
                    self.auth_token = login_response.json()["access_token"]
                    print("✅ Login successful")
                else:
                    print("❌ Login failed after registration")
                    return False
            else:
                print(f"❌ Registration failed: {register_response.text}")
                return False
        
        # Set authorization header
        self.session.headers.update({
            "Authorization": f"Bearer {self.auth_token}"
        })
        return True
    
    def test_available_symbols(self):
        """Test available symbols endpoint."""
        print("\n📊 Testing available symbols...")
        
        response = self.session.get(f"{API_BASE}/charts/available-symbols")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['total_symbols']} symbols")
            
            # Update test symbol if available
            if data['symbols']:
                self.test_symbol = data['symbols'][0]['symbol']
                print(f"📈 Using symbol: {self.test_symbol}")
            
            return True
        else:
            print(f"❌ Failed to get symbols: {response.status_code} - {response.text}")
            return False
    
    def test_available_timeframes(self):
        """Test available timeframes endpoint."""
        print(f"\n⏰ Testing available timeframes for {self.test_symbol}...")
        
        response = self.session.get(f"{API_BASE}/charts/timeframes/{self.test_symbol}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['total_timeframes']} timeframes")
            
            # Update test timeframe if available
            if data['timeframes']:
                self.test_timeframe = data['timeframes'][0]['timeframe']
                print(f"📊 Using timeframe: {self.test_timeframe}")
            
            return True
        else:
            print(f"❌ Failed to get timeframes: {response.status_code} - {response.text}")
            return False
    
    def test_candlestick_data(self):
        """Test candlestick data endpoint."""
        print(f"\n🕯️ Testing candlestick data for {self.test_symbol}...")
        
        response = self.session.get(
            f"{API_BASE}/charts/candlestick/{self.test_symbol}",
            params={
                "timeframe": self.test_timeframe,
                "limit": 100
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got {data['count']} candlesticks")
            print(f"📅 From {data['start_time']} to {data['end_time']}")
            
            # Show sample data
            if data['data']:
                sample = data['data'][0]
                print(f"📊 Sample candle: O={sample['open']}, H={sample['high']}, L={sample['low']}, C={sample['close']}, V={sample['volume']}")
            
            return True
        else:
            print(f"❌ Failed to get candlestick data: {response.status_code} - {response.text}")
            return False
    
    def test_price_history(self):
        """Test price history endpoint."""
        print(f"\n📈 Testing price history for {self.test_symbol}...")
        
        response = self.session.get(
            f"{API_BASE}/charts/price-history/{self.test_symbol}",
            params={
                "timeframe": self.test_timeframe,
                "limit": 100
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got {data['count']} price points")
            
            # Show sample data
            if data['prices']:
                sample = data['prices'][0]
                print(f"💰 Sample price: {sample['price']} at {sample['timestamp']}")
            
            return True
        else:
            print(f"❌ Failed to get price history: {response.status_code} - {response.text}")
            return False
    
    def test_volume_data(self):
        """Test volume data endpoint."""
        print(f"\n📊 Testing volume data for {self.test_symbol}...")
        
        response = self.session.get(
            f"{API_BASE}/charts/volume/{self.test_symbol}",
            params={
                "timeframe": self.test_timeframe,
                "limit": 100
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got {data['count']} volume points")
            
            # Show sample data
            if data['data']:
                sample = data['data'][0]
                print(f"📊 Sample volume: {sample['volume']} (trades: {sample['trades_count']})")
            
            return True
        else:
            print(f"❌ Failed to get volume data: {response.status_code} - {response.text}")
            return False
    
    def test_chart_summary(self):
        """Test chart summary endpoint."""
        print(f"\n📋 Testing chart summary for {self.test_symbol}...")
        
        response = self.session.get(
            f"{API_BASE}/charts/summary/{self.test_symbol}",
            params={"timeframe": self.test_timeframe}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got chart summary")
            print(f"💰 Current price: {data['current_price']}")
            print(f"📈 24h change: {data['price_change']} ({data['price_change_percentage']:.2f}%)")
            print(f"📊 Volume 24h: {data['volume_24h']}")
            print(f"🔝 High 24h: {data['high_24h']}")
            print(f"🔻 Low 24h: {data['low_24h']}")
            
            return True
        else:
            print(f"❌ Failed to get chart summary: {response.status_code} - {response.text}")
            return False
    
    def test_technical_indicators(self):
        """Test technical indicators endpoint."""
        print(f"\n🔬 Testing technical indicators for {self.test_symbol}...")
        
        # Test individual indicator
        response = self.session.get(
            f"{API_BASE}/charts/indicators/{self.test_symbol}/RSI",
            params={
                "timeframe": self.test_timeframe,
                "limit": 50
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got RSI data: {data['count']} points")
            print(f"📊 Overbought: {data['overbought_level']}, Oversold: {data['oversold_level']}")
            
            # Show sample data
            if data['data']:
                sample = data['data'][0]
                print(f"📈 Sample RSI: {sample['value']} (signal: {sample['signal']})")
        else:
            print(f"❌ Failed to get RSI data: {response.status_code} - {response.text}")
        
        # Test all indicators
        print("\n🔬 Testing all technical indicators...")
        response = self.session.get(
            f"{API_BASE}/charts/indicators/{self.test_symbol}/all",
            params={
                "timeframe": self.test_timeframe,
                "limit": 50
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got {len(data)} indicators: {list(data.keys())}")
            
            for indicator_name, indicator_data in data.items():
                print(f"📊 {indicator_name}: {indicator_data['count']} points")
            
            return True
        else:
            print(f"❌ Failed to get all indicators: {response.status_code} - {response.text}")
            return False
    
    def test_comprehensive_chart_data(self):
        """Test comprehensive chart data endpoint."""
        print(f"\n🎯 Testing comprehensive chart data for {self.test_symbol}...")
        
        chart_request = {
            "symbol": self.test_symbol,
            "timeframe": self.test_timeframe,
            "limit": 100,
            "indicators": ["RSI", "MACD", "SMA_20", "SMA_50"]
        }
        
        response = self.session.post(
            f"{API_BASE}/charts/comprehensive/{self.test_symbol}",
            json=chart_request
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Got comprehensive chart data")
            print(f"📊 Candlesticks: {data['candlestick']['count']}")
            print(f"📊 Volume: {data['volume']['count']}")
            print(f"📊 Indicators: {len(data['indicators'])}")
            print(f"📊 Available indicators: {data['metadata']['available_indicators']}")
            
            return True
        else:
            print(f"❌ Failed to get comprehensive data: {response.status_code} - {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all chart API tests."""
        print("🚀 Starting Charts API Tests")
        print("=" * 50)
        
        # Authenticate
        if not self.authenticate():
            print("❌ Authentication failed. Exiting.")
            return False
        
        # Run tests
        tests = [
            self.test_available_symbols,
            self.test_available_timeframes,
            self.test_candlestick_data,
            self.test_price_history,
            self.test_volume_data,
            self.test_chart_summary,
            self.test_technical_indicators,
            self.test_comprehensive_chart_data
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed. Check the output above.")
        
        return passed == total


def main():
    """Main function."""
    print("Charts API Tester")
    print("Make sure the server is running on http://localhost:8000")
    print("Press Enter to continue...")
    input()
    
    tester = ChartsAPITester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All chart APIs are working correctly!")
        print("\n📚 Available Chart API Endpoints:")
        print("• GET /api/v1/charts/available-symbols - Get available symbols")
        print("• GET /api/v1/charts/timeframes/{symbol} - Get available timeframes")
        print("• GET /api/v1/charts/candlestick/{symbol} - Get candlestick data")
        print("• GET /api/v1/charts/price-history/{symbol} - Get price history")
        print("• GET /api/v1/charts/volume/{symbol} - Get volume data")
        print("• GET /api/v1/charts/summary/{symbol} - Get chart summary")
        print("• GET /api/v1/charts/indicators/{symbol}/{indicator} - Get specific indicator")
        print("• GET /api/v1/charts/indicators/{symbol}/all - Get all indicators")
        print("• POST /api/v1/charts/comprehensive/{symbol} - Get comprehensive chart data")
    else:
        print("\n❌ Some tests failed. Check the server logs for details.")


if __name__ == "__main__":
    main()
