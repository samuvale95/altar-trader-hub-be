#!/usr/bin/env python3
"""
Heroku Scheduler Tasks

This script contains tasks that can be scheduled using Heroku Scheduler.
Each function can be called individually as a scheduled job.

Usage in Heroku Scheduler:
- python heroku_scheduler.py collect_crypto_data
- python heroku_scheduler.py cleanup_old_data
- python heroku_scheduler.py execute_strategies
"""

import sys
import asyncio
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def collect_crypto_data():
    """
    Collect cryptocurrency market data from exchanges.
    Run this every 1-5 minutes depending on your needs.
    
    Heroku Scheduler command:
    python heroku_scheduler.py collect_crypto_data
    """
    logger.info("Starting crypto data collection...")
    
    try:
        from app.services.data_collector import DataCollectorService
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            collector = DataCollectorService(db)
            
            # Collect data for major pairs
            symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT']
            
            for symbol in symbols:
                try:
                    asyncio.run(collector.collect_market_data(
                        exchange='binance',
                        symbol=symbol,
                        timeframe='1m'
                    ))
                    logger.info(f"Collected data for {symbol}")
                except Exception as e:
                    logger.error(f"Error collecting {symbol}: {e}")
            
            logger.info("Crypto data collection completed successfully")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in collect_crypto_data: {e}")
        sys.exit(1)


def cleanup_old_data():
    """
    Cleanup old market data to save database space.
    Run this once a day.
    
    Heroku Scheduler command:
    python heroku_scheduler.py cleanup_old_data
    """
    logger.info("Starting data cleanup...")
    
    try:
        from app.core.database import SessionLocal
        from app.models.market_data import MarketData
        from sqlalchemy import delete
        
        db = SessionLocal()
        try:
            # Delete data older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            stmt = delete(MarketData).where(MarketData.timestamp < cutoff_date)
            result = db.execute(stmt)
            db.commit()
            
            logger.info(f"Deleted {result.rowcount} old market data records")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in cleanup_old_data: {e}")
        sys.exit(1)


def execute_strategies():
    """
    Execute active trading strategies.
    Run this every 5-15 minutes depending on your strategy timeframes.
    
    Heroku Scheduler command:
    python heroku_scheduler.py execute_strategies
    """
    logger.info("Starting strategy execution...")
    
    try:
        from app.services.strategy_executor import StrategyExecutor
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            executor = StrategyExecutor(db)
            
            # Execute all active strategies
            asyncio.run(executor.execute_all_strategies())
            
            logger.info("Strategy execution completed successfully")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error in execute_strategies: {e}")
        sys.exit(1)


def health_check():
    """
    Perform a health check of the system.
    Run this every hour.
    
    Heroku Scheduler command:
    python heroku_scheduler.py health_check
    """
    logger.info("Starting health check...")
    
    try:
        from app.core.database import engine, redis_client
        
        # Check database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database: OK")
        
        # Check Redis connection (if available)
        if redis_client:
            redis_client.ping()
            logger.info("Redis: OK")
        else:
            logger.info("Redis: Not configured (optional)")
        
        logger.info("Health check completed successfully")
        
    except Exception as e:
        logger.error(f"Error in health_check: {e}")
        sys.exit(1)


def update_exchange_symbols():
    """
    Update available trading symbols from exchanges.
    Run this once a day.
    
    Heroku Scheduler command:
    python heroku_scheduler.py update_exchange_symbols
    """
    logger.info("Starting exchange symbols update...")
    
    try:
        from app.services.exchange_service import ExchangeService
        
        exchange_service = ExchangeService()
        
        # Update symbols for each exchange
        exchanges = ['binance', 'kraken', 'kucoin']
        
        for exchange_name in exchanges:
            try:
                symbols = asyncio.run(exchange_service.get_available_symbols(exchange_name))
                logger.info(f"Updated {len(symbols)} symbols for {exchange_name}")
            except Exception as e:
                logger.error(f"Error updating symbols for {exchange_name}: {e}")
        
        logger.info("Exchange symbols update completed")
        
    except Exception as e:
        logger.error(f"Error in update_exchange_symbols: {e}")
        sys.exit(1)


# Map of available tasks
TASKS = {
    'collect_crypto_data': collect_crypto_data,
    'cleanup_old_data': cleanup_old_data,
    'execute_strategies': execute_strategies,
    'health_check': health_check,
    'update_exchange_symbols': update_exchange_symbols,
}


def main():
    """Main entry point for the scheduler script."""
    if len(sys.argv) < 2:
        print("Usage: python heroku_scheduler.py <task_name>")
        print("\nAvailable tasks:")
        for task_name in TASKS.keys():
            print(f"  - {task_name}")
        sys.exit(1)
    
    task_name = sys.argv[1]
    
    if task_name not in TASKS:
        print(f"Error: Unknown task '{task_name}'")
        print("\nAvailable tasks:")
        for task_name in TASKS.keys():
            print(f"  - {task_name}")
        sys.exit(1)
    
    # Execute the task
    task_func = TASKS[task_name]
    task_func()


if __name__ == "__main__":
    main()

