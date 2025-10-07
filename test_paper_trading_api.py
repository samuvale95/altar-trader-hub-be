#!/usr/bin/env python3
"""
Test script for paper trading API.
"""

import asyncio
import aiohttp
import json


async def test_paper_trading_api():
    """Test the complete paper trading flow."""
    
    base_url = "http://localhost:8000"
    
    # You'll need to replace this with a valid token
    # Get it by calling POST /api/v1/auth/login first
    token = "YOUR_JWT_TOKEN_HERE"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        
        print("🚀 Testing Paper Trading API")
        print("=" * 60)
        
        portfolio_id = None
        position_id = None
        
        # Test 1: Create portfolio
        print("\n1. Creating Paper Portfolio")
        try:
            async with session.post(
                f"{base_url}/api/v1/paper-trading/portfolio",
                json={
                    "name": "Test Portfolio",
                    "description": "Testing paper trading system",
                    "initial_capital": 10000.00
                },
                headers=headers
            ) as response:
                if response.status == 201:
                    portfolio = await response.json()
                    portfolio_id = portfolio['id']
                    print("✅ Portfolio created successfully")
                    print(f"   ID: {portfolio_id}")
                    print(f"   Name: {portfolio['name']}")
                    print(f"   Initial Capital: ${portfolio['initial_capital']}")
                    print(f"   Cash Balance: ${portfolio['cash_balance']}")
                else:
                    print(f"❌ Failed to create portfolio: {response.status}")
                    error = await response.text()
                    print(f"   Error: {error}")
                    return
        except Exception as e:
            print(f"❌ Error creating portfolio: {e}")
            return
        
        # Test 2: Get portfolio details
        print(f"\n2. Getting Portfolio Details (ID: {portfolio_id})")
        try:
            async with session.get(
                f"{base_url}/api/v1/paper-trading/portfolio/{portfolio_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    portfolio = await response.json()
                    print("✅ Portfolio retrieved successfully")
                    print(f"   Total Value: ${portfolio['total_value']}")
                    print(f"   Total P&L: ${portfolio['total_pnl']} ({portfolio['total_pnl_percentage']}%)")
                    print(f"   Win Rate: {portfolio['win_rate']}%")
                else:
                    print(f"❌ Failed to get portfolio: {response.status}")
        except Exception as e:
            print(f"❌ Error getting portfolio: {e}")
        
        # Test 3: Buy BTC
        print(f"\n3. Buying 0.01 BTC")
        try:
            async with session.post(
                f"{base_url}/api/v1/paper-trading/portfolio/{portfolio_id}/buy",
                json={
                    "symbol": "BTCUSDT",
                    "quantity": 0.01,
                    "order_type": "MARKET"
                },
                headers=headers
            ) as response:
                if response.status == 200:
                    trade = await response.json()
                    print("✅ Buy order executed")
                    print(f"   Symbol: {trade['symbol']}")
                    print(f"   Quantity: {trade['quantity']}")
                    print(f"   Price: ${trade['price']}")
                    print(f"   Total Cost: ${trade['total_cost']}")
                    print(f"   Fee: ${trade['fee']}")
                else:
                    print(f"❌ Failed to execute buy: {response.status}")
                    error = await response.text()
                    print(f"   Error: {error}")
        except Exception as e:
            print(f"❌ Error executing buy: {e}")
        
        # Test 4: Buy ETH
        print(f"\n4. Buying 0.5 ETH")
        try:
            async with session.post(
                f"{base_url}/api/v1/paper-trading/portfolio/{portfolio_id}/buy",
                json={
                    "symbol": "ETHUSDT",
                    "quantity": 0.5,
                    "order_type": "MARKET"
                },
                headers=headers
            ) as response:
                if response.status == 200:
                    trade = await response.json()
                    print("✅ Buy order executed")
                    print(f"   Symbol: {trade['symbol']}")
                    print(f"   Quantity: {trade['quantity']}")
                    print(f"   Price: ${trade['price']}")
                    print(f"   Total Cost: ${trade['total_cost']}")
                else:
                    print(f"❌ Failed to execute buy: {response.status}")
        except Exception as e:
            print(f"❌ Error executing buy: {e}")
        
        # Test 5: Get positions
        print(f"\n5. Getting Positions")
        try:
            async with session.get(
                f"{base_url}/api/v1/paper-trading/portfolio/{portfolio_id}/positions",
                headers=headers
            ) as response:
                if response.status == 200:
                    positions = await response.json()
                    print(f"✅ Retrieved {len(positions)} positions")
                    for pos in positions:
                        position_id = pos['id']  # Save for later tests
                        pnl_indicator = "🟢" if pos['unrealized_pnl'] >= 0 else "🔴"
                        print(f"   {pnl_indicator} {pos['symbol']}: {pos['quantity']} @ ${pos['current_price']}")
                        print(f"      P&L: ${pos['unrealized_pnl']} ({pos['unrealized_pnl_percentage']}%)")
                else:
                    print(f"❌ Failed to get positions: {response.status}")
        except Exception as e:
            print(f"❌ Error getting positions: {e}")
        
        # Test 6: Get balance
        print(f"\n6. Getting Portfolio Balance")
        try:
            async with session.get(
                f"{base_url}/api/v1/paper-trading/portfolio/{portfolio_id}/balance",
                headers=headers
            ) as response:
                if response.status == 200:
                    balance_data = await response.json()
                    print("✅ Balance retrieved successfully")
                    for balance in balance_data.get('balances', []):
                        print(f"   {balance['asset']}: {balance['total']} (${balance['usd_value']})")
                else:
                    print(f"❌ Failed to get balance: {response.status}")
        except Exception as e:
            print(f"❌ Error getting balance: {e}")
        
        # Test 7: Set stop loss
        if position_id:
            print(f"\n7. Setting Stop Loss for Position {position_id}")
            try:
                async with session.put(
                    f"{base_url}/api/v1/paper-trading/portfolio/{portfolio_id}/position/{position_id}/stop-loss",
                    json={"stop_loss_price": 120000.00},
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print("✅ Stop loss set successfully")
                        print(f"   {result['message']}")
                        print(f"   Stop Loss: ${result['stop_loss_price']}")
                    else:
                        print(f"❌ Failed to set stop loss: {response.status}")
            except Exception as e:
                print(f"❌ Error setting stop loss: {e}")
        
        # Test 8: Set take profit
        if position_id:
            print(f"\n8. Setting Take Profit for Position {position_id}")
            try:
                async with session.put(
                    f"{base_url}/api/v1/paper-trading/portfolio/{portfolio_id}/position/{position_id}/take-profit",
                    json={"take_profit_price": 135000.00},
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print("✅ Take profit set successfully")
                        print(f"   {result['message']}")
                        print(f"   Take Profit: ${result['take_profit_price']}")
                    else:
                        print(f"❌ Failed to set take profit: {response.status}")
            except Exception as e:
                print(f"❌ Error setting take profit: {e}")
        
        # Test 9: Sell partial position
        print(f"\n9. Selling 0.005 BTC (partial)")
        try:
            async with session.post(
                f"{base_url}/api/v1/paper-trading/portfolio/{portfolio_id}/sell",
                json={
                    "symbol": "BTCUSDT",
                    "quantity": 0.005,
                    "order_type": "MARKET"
                },
                headers=headers
            ) as response:
                if response.status == 200:
                    trade = await response.json()
                    print("✅ Sell order executed")
                    print(f"   Symbol: {trade['symbol']}")
                    print(f"   Quantity: {trade['quantity']}")
                    print(f"   Price: ${trade['price']}")
                    print(f"   Realized P&L: ${trade.get('realized_pnl', 0)} ({trade.get('realized_pnl_percentage', 0)}%)")
                else:
                    print(f"❌ Failed to execute sell: {response.status}")
                    error = await response.text()
                    print(f"   Error: {error}")
        except Exception as e:
            print(f"❌ Error executing sell: {e}")
        
        # Test 10: Get trade history
        print(f"\n10. Getting Trade History")
        try:
            async with session.get(
                f"{base_url}/api/v1/paper-trading/portfolio/{portfolio_id}/trades?limit=10",
                headers=headers
            ) as response:
                if response.status == 200:
                    trades = await response.json()
                    print(f"✅ Retrieved {len(trades)} trades")
                    for trade in trades[:5]:  # Show first 5
                        side_indicator = "🟢" if trade['side'] == 'BUY' else "🔴"
                        print(f"   {side_indicator} {trade['side']} {trade['quantity']} {trade['symbol']} @ ${trade['price']}")
                        if trade['side'] == 'SELL' and trade.get('realized_pnl'):
                            print(f"      P&L: ${trade['realized_pnl']} ({trade['realized_pnl_percentage']}%)")
                else:
                    print(f"❌ Failed to get trade history: {response.status}")
        except Exception as e:
            print(f"❌ Error getting trade history: {e}")
        
        # Test 11: Update portfolio value
        print(f"\n11. Updating Portfolio Value")
        try:
            async with session.post(
                f"{base_url}/api/v1/paper-trading/portfolio/{portfolio_id}/update-value",
                headers=headers
            ) as response:
                if response.status == 200:
                    summary = await response.json()
                    print("✅ Portfolio value updated")
                    print(f"   Cash: ${summary['cash_balance']}")
                    print(f"   Invested: ${summary['invested_value']}")
                    print(f"   Total Value: ${summary['total_value']}")
                    print(f"   Total P&L: ${summary['total_pnl']} ({summary['total_pnl_percentage']}%)")
                    print(f"   Unrealized P&L: ${summary['unrealized_pnl']}")
                else:
                    print(f"❌ Failed to update portfolio value: {response.status}")
        except Exception as e:
            print(f"❌ Error updating portfolio value: {e}")
        
        # Test 12: Get updated portfolio
        print(f"\n12. Final Portfolio Status")
        try:
            async with session.get(
                f"{base_url}/api/v1/paper-trading/portfolio/{portfolio_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    portfolio = await response.json()
                    print("✅ Final portfolio status")
                    print(f"   Name: {portfolio['name']}")
                    print(f"   Mode: {portfolio['mode']}")
                    print(f"   Initial Capital: ${portfolio['initial_capital']}")
                    print(f"   Current Value: ${portfolio['total_value']}")
                    print(f"   Cash: ${portfolio['cash_balance']}")
                    print(f"   Invested: ${portfolio['invested_value']}")
                    print(f"   Total P&L: ${portfolio['total_pnl']} ({portfolio['total_pnl_percentage']}%)")
                    print(f"   Realized P&L: ${portfolio['realized_pnl']}")
                    print(f"   Unrealized P&L: ${portfolio['unrealized_pnl']}")
                    print(f"   Total Trades: {portfolio['total_trades']}")
                    print(f"   Win Rate: {portfolio['win_rate']}%")
                    print(f"   Max Drawdown: {portfolio['max_drawdown']}%")
                else:
                    print(f"❌ Failed to get final portfolio: {response.status}")
        except Exception as e:
            print(f"❌ Error getting final portfolio: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 Paper Trading API test completed!")
        print("\nNote: Update the token variable with a valid JWT token to run this test")


if __name__ == "__main__":
    asyncio.run(test_paper_trading_api())

