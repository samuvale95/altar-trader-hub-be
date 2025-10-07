#!/usr/bin/env python3
"""
Test script for scheduler management API.
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_scheduler_management_api():
    """Test the scheduler management API endpoints."""
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        
        print("🚀 Testing Scheduler Management API")
        print("=" * 50)
        
        # Test 1: Get scheduler status
        print("\n1. Testing GET /api/v1/data-collector/status")
        try:
            async with session.get(
                f"{base_url}/api/v1/data-collector/status"
            ) as response:
                if response.status == 200:
                    status = await response.json()
                    print("✅ Scheduler status retrieved successfully")
                    print(f"   Scheduler running: {status.get('scheduler', {}).get('is_running')}")
                    print(f"   Collection interval: {status.get('scheduler', {}).get('collection_interval')}s")
                    print(f"   Active tasks: {status.get('scheduler', {}).get('active_tasks_count')}")
                    print(f"   Symbols count: {status.get('data_feeder', {}).get('symbols_count')}")
                else:
                    print(f"❌ Failed to get status: {response.status}")
        except Exception as e:
            print(f"❌ Error getting status: {e}")
        
        # Test 2: Get scheduler configuration
        print("\n2. Testing GET /api/v1/data-collector/config")
        try:
            async with session.get(
                f"{base_url}/api/v1/data-collector/config"
            ) as response:
                if response.status == 200:
                    config = await response.json()
                    print("✅ Scheduler configuration retrieved successfully")
                    print(f"   Collection interval: {config.get('collection_interval')}s")
                    print(f"   Symbol refresh interval: {config.get('symbol_refresh_interval')}s")
                    print(f"   Is running: {config.get('is_running')}")
                    print(f"   Symbols: {config.get('symbols', [])[:5]}...")
                    print(f"   Timeframes: {config.get('timeframes')}")
                    print(f"   Available symbols: {len(config.get('available_symbols', []))}")
                else:
                    print(f"❌ Failed to get config: {response.status}")
        except Exception as e:
            print(f"❌ Error getting config: {e}")
        
        # Test 3: Update configuration
        print("\n3. Testing PUT /api/v1/data-collector/config")
        test_config = {
            "collection_interval": 600,  # 10 minutes
            "symbols": ["BTCUSDT", "ETHUSDT", "ADAUSDT"],
            "timeframes": ["1m", "5m", "1h"]
        }
        try:
            async with session.put(
                f"{base_url}/api/v1/data-collector/config",
                json=test_config,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Configuration updated successfully")
                    print(f"   Message: {result.get('message')}")
                    print(f"   New collection interval: {result.get('config', {}).get('collection_interval')}s")
                    print(f"   New symbols: {result.get('config', {}).get('symbols')}")
                    print(f"   New timeframes: {result.get('config', {}).get('timeframes')}")
                else:
                    print(f"❌ Failed to update config: {response.status}")
                    error_text = await response.text()
                    print(f"   Error: {error_text}")
        except Exception as e:
            print(f"❌ Error updating config: {e}")
        
        # Test 4: Start scheduler
        print("\n4. Testing POST /api/v1/data-collector/start")
        try:
            async with session.post(
                f"{base_url}/api/v1/data-collector/start"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Scheduler start command sent")
                    print(f"   Message: {result.get('message')}")
                else:
                    print(f"❌ Failed to start scheduler: {response.status}")
        except Exception as e:
            print(f"❌ Error starting scheduler: {e}")
        
        # Test 5: Stop scheduler
        print("\n5. Testing POST /api/v1/data-collector/stop")
        try:
            async with session.post(
                f"{base_url}/api/v1/data-collector/stop"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Scheduler stop command sent")
                    print(f"   Message: {result.get('message')}")
                else:
                    print(f"❌ Failed to stop scheduler: {response.status}")
        except Exception as e:
            print(f"❌ Error stopping scheduler: {e}")
        
        # Test 6: Restart scheduler
        print("\n6. Testing scheduler restart sequence")
        try:
            # Stop first
            async with session.post(f"{base_url}/api/v1/data-collector/stop") as response:
                if response.status == 200:
                    print("   ✅ Scheduler stopped")
            
            # Wait a moment
            await asyncio.sleep(1)
            
            # Start again
            async with session.post(f"{base_url}/api/v1/data-collector/start") as response:
                if response.status == 200:
                    print("   ✅ Scheduler restarted")
                    
                    # Check status
                    async with session.get(f"{base_url}/api/v1/data-collector/status") as response:
                        if response.status == 200:
                            status = await response.json()
                            print(f"   ✅ Scheduler running: {status.get('scheduler', {}).get('is_running')}")
                
        except Exception as e:
            print(f"❌ Error in restart sequence: {e}")
        
        # Test 7: Refresh symbols
        print("\n7. Testing POST /api/v1/data-collector/refresh-symbols")
        try:
            async with session.post(
                f"{base_url}/api/v1/data-collector/refresh-symbols"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ Symbol refresh started")
                    print(f"   Task ID: {result.get('task_id')}")
                    print(f"   Status: {result.get('status')}")
                else:
                    print(f"❌ Failed to refresh symbols: {response.status}")
        except Exception as e:
            print(f"❌ Error refreshing symbols: {e}")
        
        # Test 8: Get tasks
        print("\n8. Testing GET /api/v1/data-collector/tasks/active")
        try:
            async with session.get(
                f"{base_url}/api/v1/data-collector/tasks/active"
            ) as response:
                if response.status == 200:
                    tasks = await response.json()
                    print(f"✅ Retrieved {len(tasks)} active tasks")
                    for task in tasks[:3]:  # Show first 3 tasks
                        print(f"   - {task.get('task_type')}: {task.get('status')} ({task.get('progress')}%)")
                else:
                    print(f"❌ Failed to get active tasks: {response.status}")
        except Exception as e:
            print(f"❌ Error getting active tasks: {e}")
        
        # Test 9: Invalid configuration
        print("\n9. Testing invalid configuration")
        invalid_config = {
            "collection_interval": 30,  # Too short
            "symbols": [],  # Empty list
            "timeframes": ["invalid"]  # Invalid timeframe
        }
        try:
            async with session.put(
                f"{base_url}/api/v1/data-collector/config",
                json=invalid_config,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 400:
                    error_data = await response.json()
                    print("✅ Invalid configuration properly rejected")
                    print(f"   Error: {error_data.get('detail')}")
                else:
                    print(f"❌ Expected 400 error, got: {response.status}")
        except Exception as e:
            print(f"❌ Error testing invalid config: {e}")
        
        # Test 10: Final status check
        print("\n10. Final status check")
        try:
            async with session.get(
                f"{base_url}/api/v1/data-collector/status"
            ) as response:
                if response.status == 200:
                    status = await response.json()
                    print("✅ Final status check")
                    print(f"   Scheduler running: {status.get('scheduler', {}).get('is_running')}")
                    print(f"   Collection interval: {status.get('scheduler', {}).get('collection_interval')}s")
                    print(f"   Active tasks: {status.get('scheduler', {}).get('active_tasks_count')}")
                    print(f"   Symbols: {len(status.get('data_feeder', {}).get('symbols', []))}")
                else:
                    print(f"❌ Failed final status check: {response.status}")
        except Exception as e:
            print(f"❌ Error in final status check: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Scheduler Management API test completed!")


if __name__ == "__main__":
    asyncio.run(test_scheduler_management_api())

