#!/usr/bin/env python3
"""
Script to collect market data for trading strategies
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.data_feeder import data_feeder
from app.core.logging import get_logger

logger = get_logger(__name__)

async def collect_market_data():
    """Collect market data for trading strategies."""
    
    print("🔍 Collecting Market Data for Trading Strategies")
    print("=" * 50)
    
    # Define symbols and timeframes for trading strategies
    symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT"]
    timeframes = ["1d", "4h", "1h", "15m", "5m", "1m"]
    
    print(f"📊 Collecting data for {len(symbols)} symbols and {len(timeframes)} timeframes")
    print(f"   Symbols: {symbols}")
    print(f"   Timeframes: {timeframes}")
    
    try:
        # Collect market data
        success = await data_feeder.collect_market_data(symbols, timeframes)
        
        if success:
            print("✅ Market data collection completed successfully")
            
            # Check collected data
            from app.core.database import SessionLocal
            from app.models.market_data import MarketData
            
            db = SessionLocal()
            try:
                total_data = db.query(MarketData).count()
                print(f"📈 Total market data records: {total_data}")
                
                # Show data by symbol
                for symbol in symbols:
                    count = db.query(MarketData).filter(MarketData.symbol == symbol).count()
                    print(f"   {symbol}: {count} records")
                
                # Show data by timeframe
                for timeframe in timeframes:
                    count = db.query(MarketData).filter(MarketData.timeframe == timeframe).count()
                    print(f"   {timeframe}: {count} records")
                    
            finally:
                db.close()
        else:
            print("❌ Market data collection failed")
            
    except Exception as e:
        print(f"❌ Error collecting market data: {e}")
        logger.error(f"Market data collection error: {e}")

async def main():
    """Main function."""
    await collect_market_data()

if __name__ == "__main__":
    asyncio.run(main())

