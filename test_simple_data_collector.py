#!/usr/bin/env python3
"""
Simple test for data collector functionality
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.data_feeder import data_feeder
from app.services.realtime_data_collector import realtime_collector

async def test_data_collector():
    """Test data collector functionality."""
    
    print("🔍 Testing Data Collector Functionality")
    print("=" * 50)
    
    # Test 1: Test data feeder get_latest_data
    print("\n📊 Test 1: Test data feeder get_latest_data")
    try:
        latest_data = await data_feeder.get_latest_data("BTCUSDT", "1m", limit=1)
        if latest_data:
            print(f"✅ Got latest data for BTCUSDT:")
            print(f"   Price: ${latest_data[0]['close_price']:.2f}")
            print(f"   Volume: {latest_data[0]['volume']:.2f}")
            print(f"   Timestamp: {latest_data[0]['timestamp']}")
        else:
            print("❌ No data returned")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: Test realtime collector
    print("\n📊 Test 2: Test realtime collector")
    try:
        # Start collection for a few symbols
        await realtime_collector.start_collection(["BTCUSDT", "ETHUSDT"])
        print("✅ Started data collection")
        
        # Wait a bit
        await asyncio.sleep(5)
        
        # Get latest prices
        latest_prices = await realtime_collector.get_latest_prices(["BTCUSDT", "ETHUSDT"])
        print(f"✅ Latest prices: {latest_prices}")
        
        # Stop collection
        await realtime_collector.stop_collection()
        print("✅ Stopped data collection")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🎉 Data collector test completed!")

async def main():
    """Main function."""
    await test_data_collector()

if __name__ == "__main__":
    asyncio.run(main())

