#!/usr/bin/env python3
"""
Script to monitor data collection in real-time
"""

import requests
import json
import time
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

def monitor_data_collection():
    """Monitor data collection continuously."""
    
    token = get_auth_token()
    if not token:
        print("❌ Failed to get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Real-time Data Collection Monitor")
    print("=" * 50)
    print("Press Ctrl+C to stop monitoring")
    print()
    
    try:
        while True:
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # Get collection status
            response = requests.get(f"{BASE_URL}/api/v1/data-collector/status", headers=headers)
            if response.status_code == 200:
                data = response.json()
                print(f"[{current_time}] Status: {'🟢 Running' if data['is_running'] else '🔴 Stopped'} | "
                      f"Symbols: {data['symbols_count']} | Tasks: {data['active_tasks']}")
            
            # Get latest prices every 30 seconds
            if int(current_time.split(':')[2]) % 30 == 0:
                response = requests.get(f"{BASE_URL}/api/v1/data-collector/latest-prices", headers=headers)
                if response.status_code == 200:
                    price_data = response.json()
                    if price_data['latest_prices']:
                        print(f"[{current_time}] Latest Prices:")
                        for symbol, data in price_data['latest_prices'].items():
                            change = f"+{data['change_24h']}%" if data['change_24h'] and data['change_24h'] > 0 else f"{data['change_24h']}%"
                            print(f"  {symbol}: ${data['price']:.2f} ({change})")
                        print()
            
            time.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

def main():
    """Main function."""
    print("🚀 Data Collection Monitor")
    print("=" * 50)
    
    monitor_data_collection()

if __name__ == "__main__":
    main()




