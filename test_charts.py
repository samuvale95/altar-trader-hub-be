#!/usr/bin/env python3
"""
Test script for charts API
"""

import requests
import json
import matplotlib.pyplot as plt
import pandas as pd
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

def test_charts_api():
    """Test charts API endpoints."""
    
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing Charts API")
    print("=" * 50)
    
    # Test 1: Get available symbols
    print("\n📊 Test 1: Get available symbols")
    response = requests.get(f"{BASE_URL}/api/v1/charts/available-symbols", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Available symbols: {data['total_symbols']}")
        for symbol in data['symbols'][:5]:  # Show first 5
            print(f"   {symbol['symbol']}: {symbol['data_points']} points, ${symbol['latest_price']:.2f}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Test 2: Get price history
    print("\n📊 Test 2: Get price history for BTCUSDT")
    response = requests.get(f"{BASE_URL}/api/v1/charts/price-history/BTCUSDT?timeframe=1m&limit=50", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Price history: {data['count']} points")
        print(f"   From: {data['start_time']}")
        print(f"   To: {data['end_time']}")
        print(f"   Latest price: ${data['prices'][-1]['price']:.2f}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Test 3: Get candlestick data
    print("\n📊 Test 3: Get candlestick data for BTCUSDT")
    response = requests.get(f"{BASE_URL}/api/v1/charts/candlestick/BTCUSDT?timeframe=5m&limit=20", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Candlestick data: {data['count']} candles")
        print(f"   From: {data['start_time']}")
        print(f"   To: {data['end_time']}")
        print(f"   Latest: O:{data['data'][-1]['open']:.2f} H:{data['data'][-1]['high']:.2f} L:{data['data'][-1]['low']:.2f} C:{data['data'][-1]['close']:.2f}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Test 4: Get volume data
    print("\n📊 Test 4: Get volume data for BTCUSDT")
    response = requests.get(f"{BASE_URL}/api/v1/charts/volume/BTCUSDT?timeframe=1m&limit=30", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Volume data: {data['count']} points")
        print(f"   Latest volume: {data['data'][-1]['volume']:.2f}")
        print(f"   Latest trades: {data['data'][-1]['trades_count']}")
    else:
        print(f"❌ Failed: {response.status_code}")
    
    # Test 5: Get available timeframes
    print("\n📊 Test 5: Get available timeframes for BTCUSDT")
    response = requests.get(f"{BASE_URL}/api/v1/charts/timeframes/BTCUSDT", headers=headers)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Available timeframes: {data['total_timeframes']}")
        for tf in data['timeframes']:
            print(f"   {tf['timeframe']}: {tf['data_points']} points")
    else:
        print(f"❌ Failed: {response.status_code}")

def create_simple_chart():
    """Create a simple chart using matplotlib."""
    
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n📈 Creating Simple Chart")
    print("=" * 30)
    
    # Get price data
    response = requests.get(f"{BASE_URL}/api/v1/charts/price-history/BTCUSDT?timeframe=1m&limit=100", headers=headers)
    if response.status_code != 200:
        print("❌ Failed to get price data")
        return
    
    data = response.json()
    
    # Convert to DataFrame
    df = pd.DataFrame(data['prices'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Create chart
    plt.figure(figsize=(12, 6))
    plt.plot(df['timestamp'], df['price'], linewidth=2, color='blue')
    plt.title(f'BTCUSDT Price History - {data["timeframe"]} timeframe')
    plt.xlabel('Time')
    plt.ylabel('Price (USDT)')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save chart
    chart_file = 'btc_price_chart.png'
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    print(f"✅ Chart saved as {chart_file}")
    
    # Show latest prices
    print(f"📊 Latest 5 prices:")
    for i, row in df.tail().iterrows():
        print(f"   {row['timestamp'].strftime('%H:%M:%S')}: ${row['price']:.2f}")

def main():
    """Main test function."""
    print("🚀 Charts API Test")
    print("=" * 50)
    
    test_charts_api()
    create_simple_chart()
    
    print("\n🎉 Charts test completed!")

if __name__ == "__main__":
    main()

