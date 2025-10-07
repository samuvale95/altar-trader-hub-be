#!/usr/bin/env python3
"""
Test script for latest-prices endpoint.
"""

import asyncio
import aiohttp
import json


async def test_latest_prices_endpoint():
    """Test the latest-prices endpoint."""
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        print("🚀 Testing Latest Prices Endpoint")
        print("=" * 50)
        
        # Test 1: Get latest prices without symbols (should return all available)
        print("\n1. Testing GET /api/v1/data-collector/latest-prices (no symbols)")
        try:
            async with session.get(
                f"{base_url}/api/v1/data-collector/latest-prices"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Latest prices retrieved successfully")
                    print(f"   Count: {result.get('count')}")
                    print(f"   Requested symbols: {result.get('requested_symbols')}")
                    print(f"   Limit: {result.get('limit')}")
                    print(f"   Calculated at: {result.get('calculated_at')}")
                    
                    prices = result.get('latest_prices', [])
                    print(f"   Sample prices:")
                    for price in prices[:5]:  # Show first 5
                        change_indicator = "🟢" if price.get('change_24h_percent', 0) > 0 else "🔴"
                        print(f"     {change_indicator} {price.get('symbol')}: ${price.get('price')} "
                              f"({price.get('change_24h_percent')}% / ${price.get('change_24h')})")
                else:
                    print(f"❌ Failed to get latest prices: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
        except Exception as e:
            print(f"❌ Error getting latest prices: {e}")
        
        # Test 2: Get latest prices for specific symbols
        print("\n2. Testing GET /api/v1/data-collector/latest-prices?symbols=BTCUSDT,ETHUSDT")
        try:
            async with session.get(
                f"{base_url}/api/v1/data-collector/latest-prices",
                params={"symbols": "BTCUSDT,ETHUSDT"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Specific symbols prices retrieved successfully")
                    print(f"   Count: {result.get('count')}")
                    print(f"   Requested symbols: {result.get('requested_symbols')}")
                    
                    prices = result.get('latest_prices', [])
                    print(f"   Prices:")
                    for price in prices:
                        change_indicator = "🟢" if price.get('change_24h_percent', 0) > 0 else "🔴"
                        print(f"     {change_indicator} {price.get('symbol')}: ${price.get('price')} "
                              f"(24h: {price.get('change_24h_percent')}% / ${price.get('change_24h')})")
                else:
                    print(f"❌ Failed to get specific symbols prices: {response.status}")
        except Exception as e:
            print(f"❌ Error getting specific symbols prices: {e}")
        
        # Test 3: Get latest prices with limit
        print("\n3. Testing GET /api/v1/data-collector/latest-prices?limit=5")
        try:
            async with session.get(
                f"{base_url}/api/v1/data-collector/latest-prices",
                params={"limit": 5}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Limited prices retrieved successfully")
                    print(f"   Count: {result.get('count')}")
                    print(f"   Limit: {result.get('limit')}")
                    
                    prices = result.get('latest_prices', [])
                    print(f"   Prices:")
                    for price in prices:
                        print(f"     - {price.get('symbol')}: ${price.get('price')}")
                else:
                    print(f"❌ Failed to get limited prices: {response.status}")
        except Exception as e:
            print(f"❌ Error getting limited prices: {e}")
        
        # Test 4: Test with invalid symbol
        print("\n4. Testing with invalid symbol")
        try:
            async with session.get(
                f"{base_url}/api/v1/data-collector/latest-prices",
                params={"symbols": "INVALIDUSDT"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Invalid symbol handled gracefully")
                    print(f"   Count: {result.get('count')}")
                    print(f"   Latest prices: {result.get('latest_prices')}")
                else:
                    print(f"❌ Unexpected error with invalid symbol: {response.status}")
        except Exception as e:
            print(f"❌ Error testing invalid symbol: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Latest Prices endpoint test completed!")


if __name__ == "__main__":
    asyncio.run(test_latest_prices_endpoint())
