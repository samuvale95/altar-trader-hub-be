#!/usr/bin/env python3
"""
Test script for async data collector endpoints.
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_data_collector_endpoints():
    """Test the async data collector endpoints."""
    
    base_url = "http://localhost:8000"
    
    # Test data
    test_data = {
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "timeframes": ["1m", "5m"]
    }
    
    async with aiohttp.ClientSession() as session:
        
        print("🚀 Testing Async Data Collector Endpoints")
        print("=" * 50)
        
        # Test 1: Start data collection
        print("\n1. Testing /api/v1/data-collector/start")
        try:
            async with session.post(
                f"{base_url}/api/v1/data-collector/start",
                json=test_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    task_id = result.get("task_id")
                    print(f"✅ Data collection started successfully")
                    print(f"   Task ID: {task_id}")
                    print(f"   Message: {result.get('message')}")
                else:
                    print(f"❌ Failed to start data collection: {response.status}")
                    return
        except Exception as e:
            print(f"❌ Error starting data collection: {e}")
            return
        
        # Test 2: Check task status
        print(f"\n2. Testing /api/v1/data-collector/task/{task_id}")
        for i in range(5):
            try:
                async with session.get(
                    f"{base_url}/api/v1/data-collector/task/{task_id}"
                ) as response:
                    if response.status == 200:
                        task_status = await response.json()
                        print(f"   Status: {task_status.get('status')}")
                        print(f"   Progress: {task_status.get('progress')}%")
                        print(f"   Message: {task_status.get('message')}")
                        
                        if task_status.get('status') in ['completed', 'failed']:
                            break
                    else:
                        print(f"❌ Failed to get task status: {response.status}")
                        break
            except Exception as e:
                print(f"❌ Error getting task status: {e}")
                break
            
            await asyncio.sleep(2)
        
        # Test 3: Get all tasks
        print("\n3. Testing /api/v1/data-collector/tasks")
        try:
            async with session.get(
                f"{base_url}/api/v1/data-collector/tasks"
            ) as response:
                if response.status == 200:
                    tasks = await response.json()
                    print(f"✅ Retrieved {len(tasks)} tasks")
                    for task in tasks[:3]:  # Show first 3 tasks
                        print(f"   - {task.get('task_type')}: {task.get('status')}")
                else:
                    print(f"❌ Failed to get tasks: {response.status}")
        except Exception as e:
            print(f"❌ Error getting tasks: {e}")
        
        # Test 4: Get active tasks
        print("\n4. Testing /api/v1/data-collector/tasks/active")
        try:
            async with session.get(
                f"{base_url}/api/v1/data-collector/tasks/active"
            ) as response:
                if response.status == 200:
                    active_tasks = await response.json()
                    print(f"✅ Retrieved {len(active_tasks)} active tasks")
                    for task in active_tasks:
                        print(f"   - {task.get('task_type')}: {task.get('progress')}%")
                else:
                    print(f"❌ Failed to get active tasks: {response.status}")
        except Exception as e:
            print(f"❌ Error getting active tasks: {e}")
        
        # Test 5: Get task stats
        print("\n5. Testing /api/v1/data-collector/tasks/stats")
        try:
            async with session.get(
                f"{base_url}/api/v1/data-collector/tasks/stats"
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"✅ Task statistics retrieved")
                    print(f"   Task counts: {stats.get('task_counts')}")
                    print(f"   Active tasks: {stats.get('active_tasks_count')}")
                    print(f"   Symbols count: {stats.get('data_collector_status', {}).get('symbols_count')}")
                else:
                    print(f"❌ Failed to get task stats: {response.status}")
        except Exception as e:
            print(f"❌ Error getting task stats: {e}")
        
        # Test 6: Refresh symbols
        print("\n6. Testing /api/v1/data-collector/refresh-symbols")
        try:
            async with session.post(
                f"{base_url}/api/v1/data-collector/refresh-symbols"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    refresh_task_id = result.get("task_id")
                    print(f"✅ Symbol refresh started")
                    print(f"   Task ID: {refresh_task_id}")
                else:
                    print(f"❌ Failed to start symbol refresh: {response.status}")
        except Exception as e:
            print(f"❌ Error starting symbol refresh: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Test completed!")


if __name__ == "__main__":
    asyncio.run(test_data_collector_endpoints())

