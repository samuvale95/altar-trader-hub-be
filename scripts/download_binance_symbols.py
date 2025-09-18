#!/usr/bin/env python3
"""
Script to download all tradable symbols from Binance API
"""

import requests
import json
import pandas as pd
from datetime import datetime
import sys
import os

def get_binance_symbols():
    """Get all tradable symbols from Binance."""
    
    try:
        # Get exchange info
        response = requests.get("https://api.binance.com/api/v3/exchangeInfo")
        response.raise_for_status()
        
        data = response.json()
        symbols = data['symbols']
        
        # Filter active symbols
        active_symbols = [
            symbol for symbol in symbols 
            if symbol['status'] == 'TRADING'
        ]
        
        return active_symbols
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

def get_24hr_ticker():
    """Get 24hr ticker data for all symbols."""
    
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/24hr")
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching ticker data: {e}")
        return None

def filter_by_quote_asset(symbols, quote_asset="USDT"):
    """Filter symbols by quote asset (e.g., USDT, BTC, ETH)."""
    
    filtered = [
        symbol for symbol in symbols 
        if symbol['quoteAsset'] == quote_asset
    ]
    
    return filtered

def save_to_csv(symbols, filename="binance_symbols.csv"):
    """Save symbols to CSV file."""
    
    # Convert to DataFrame
    df_data = []
    for symbol in symbols:
        df_data.append({
            'symbol': symbol['symbol'],
            'base_asset': symbol['baseAsset'],
            'quote_asset': symbol['quoteAsset'],
            'status': symbol['status'],
            'is_spot_trading_allowed': symbol['isSpotTradingAllowed'],
            'is_margin_trading_allowed': symbol['isMarginTradingAllowed'],
            'is_futures_trading_allowed': symbol.get('isFuturesTradingAllowed', False),
            'filters': json.dumps(symbol['filters'])
        })
    
    df = pd.DataFrame(df_data)
    df.to_csv(filename, index=False)
    print(f"Symbols saved to {filename}")
    
    return df

def save_to_json(symbols, filename="binance_symbols.json"):
    """Save symbols to JSON file."""
    
    with open(filename, 'w') as f:
        json.dump(symbols, f, indent=2)
    
    print(f"Symbols saved to {filename}")

def main():
    """Main function."""
    
    print("🔍 Downloading Binance symbols...")
    
    # Get all symbols
    symbols = get_binance_symbols()
    if not symbols:
        print("❌ Failed to download symbols")
        sys.exit(1)
    
    print(f"✅ Downloaded {len(symbols)} symbols")
    
    # Filter by quote asset
    quote_assets = ["USDT", "BTC", "ETH", "BNB"]
    
    for quote_asset in quote_assets:
        filtered_symbols = filter_by_quote_asset(symbols, quote_asset)
        print(f"📊 {quote_asset} pairs: {len(filtered_symbols)}")
        
        if filtered_symbols:
            # Save to CSV
            csv_filename = f"binance_{quote_asset.lower()}_pairs.csv"
            save_to_csv(filtered_symbols, csv_filename)
            
            # Save to JSON
            json_filename = f"binance_{quote_asset.lower()}_pairs.json"
            save_to_json(filtered_symbols, json_filename)
    
    # Get 24hr ticker data
    print("\n📈 Downloading 24hr ticker data...")
    ticker_data = get_24hr_ticker()
    
    if ticker_data:
        # Convert to DataFrame
        ticker_df = pd.DataFrame(ticker_data)
        
        # Save ticker data
        ticker_df.to_csv("binance_24hr_ticker.csv", index=False)
        print("✅ 24hr ticker data saved to binance_24hr_ticker.csv")
        
        # Show top 10 by volume
        ticker_df['volume'] = pd.to_numeric(ticker_df['volume'])
        top_volume = ticker_df.nlargest(10, 'volume')[['symbol', 'volume', 'priceChangePercent']]
        print("\n🏆 Top 10 by volume:")
        print(top_volume.to_string(index=False))
    
    print("\n🎉 Download completed!")

if __name__ == "__main__":
    main()
