"""
Migration script to add trading strategy tables
"""

from sqlalchemy import create_engine, text
import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to add trading strategy tables."""
    
    # Create engine
    engine = create_engine(settings.database_url)
    
    # SQL statements to create tables
    sql_statements = [
        """
        CREATE TABLE IF NOT EXISTS trading_strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            strategy_type VARCHAR(50) NOT NULL,
            parameters JSON NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            initial_balance DECIMAL(20,8) NOT NULL DEFAULT 10000.0,
            commission_rate DECIMAL(10,6) NOT NULL DEFAULT 0.001,
            status VARCHAR(20) NOT NULL DEFAULT 'inactive',
            is_active BOOLEAN NOT NULL DEFAULT 0,
            auto_start BOOLEAN NOT NULL DEFAULT 0,
            current_balance DECIMAL(20,8) NOT NULL DEFAULT 0,
            total_equity DECIMAL(20,8) NOT NULL DEFAULT 0,
            total_return DECIMAL(10,6) NOT NULL DEFAULT 0,
            total_trades INTEGER NOT NULL DEFAULT 0,
            win_rate DECIMAL(5,4) NOT NULL DEFAULT 0,
            max_drawdown DECIMAL(10,6) NOT NULL DEFAULT 0,
            sharpe_ratio DECIMAL(10,6) NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME,
            last_run_at DATETIME,
            started_at DATETIME,
            stopped_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS backtest_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            start_date DATETIME NOT NULL,
            end_date DATETIME NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            total_periods INTEGER NOT NULL DEFAULT 0,
            initial_balance DECIMAL(20,8) NOT NULL,
            final_balance DECIMAL(20,8) NOT NULL DEFAULT 0,
            total_equity DECIMAL(20,8) NOT NULL DEFAULT 0,
            total_return DECIMAL(10,6) NOT NULL DEFAULT 0,
            annualized_return DECIMAL(10,6) NOT NULL DEFAULT 0,
            volatility DECIMAL(10,6) NOT NULL DEFAULT 0,
            sharpe_ratio DECIMAL(10,6) NOT NULL DEFAULT 0,
            max_drawdown DECIMAL(10,6) NOT NULL DEFAULT 0,
            win_rate DECIMAL(5,4) NOT NULL DEFAULT 0,
            total_trades INTEGER NOT NULL DEFAULT 0,
            buy_trades INTEGER NOT NULL DEFAULT 0,
            sell_trades INTEGER NOT NULL DEFAULT 0,
            buy_hold_return DECIMAL(10,6) NOT NULL DEFAULT 0,
            outperformance DECIMAL(10,6) NOT NULL DEFAULT 0,
            avg_trade_size DECIMAL(20,8) NOT NULL DEFAULT 0,
            trade_frequency DECIMAL(10,6) NOT NULL DEFAULT 0,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            started_at DATETIME,
            completed_at DATETIME,
            FOREIGN KEY (strategy_id) REFERENCES trading_strategies (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS strategy_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            side VARCHAR(10) NOT NULL,
            quantity DECIMAL(20,8) NOT NULL,
            price DECIMAL(20,8) NOT NULL,
            commission DECIMAL(20,8) NOT NULL DEFAULT 0,
            signal_strength DECIMAL(5,4) NOT NULL DEFAULT 0,
            reason TEXT,
            executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES trading_strategies (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS backtest_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            backtest_id INTEGER NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            side VARCHAR(10) NOT NULL,
            quantity DECIMAL(20,8) NOT NULL,
            price DECIMAL(20,8) NOT NULL,
            commission DECIMAL(20,8) NOT NULL DEFAULT 0,
            signal_strength DECIMAL(5,4) NOT NULL DEFAULT 0,
            reason TEXT,
            executed_at DATETIME NOT NULL,
            FOREIGN KEY (backtest_id) REFERENCES backtest_results (id)
        )
        """,
        
        """
        CREATE TABLE IF NOT EXISTS strategy_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            action VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL,
            message TEXT,
            balance DECIMAL(20,8) NOT NULL DEFAULT 0,
            equity DECIMAL(20,8) NOT NULL DEFAULT 0,
            total_trades INTEGER NOT NULL DEFAULT 0,
            executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES trading_strategies (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """
    ]
    
    # Create indexes
    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_trading_strategies_user_id ON trading_strategies (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_trading_strategies_status ON trading_strategies (status)",
        "CREATE INDEX IF NOT EXISTS idx_trading_strategies_strategy_type ON trading_strategies (strategy_type)",
        "CREATE INDEX IF NOT EXISTS idx_backtest_results_user_id ON backtest_results (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_backtest_results_strategy_id ON backtest_results (strategy_id)",
        "CREATE INDEX IF NOT EXISTS idx_backtest_results_status ON backtest_results (status)",
        "CREATE INDEX IF NOT EXISTS idx_strategy_trades_strategy_id ON strategy_trades (strategy_id)",
        "CREATE INDEX IF NOT EXISTS idx_strategy_trades_user_id ON strategy_trades (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_strategy_trades_executed_at ON strategy_trades (executed_at)",
        "CREATE INDEX IF NOT EXISTS idx_backtest_trades_backtest_id ON backtest_trades (backtest_id)",
        "CREATE INDEX IF NOT EXISTS idx_strategy_executions_strategy_id ON strategy_executions (strategy_id)",
        "CREATE INDEX IF NOT EXISTS idx_strategy_executions_user_id ON strategy_executions (user_id)"
    ]
    
    try:
        with engine.connect() as conn:
            # Execute table creation statements
            for sql in sql_statements:
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"Executed: {sql[:50]}...")
            
            # Execute index creation statements
            for sql in index_statements:
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"Created index: {sql}")
            
            logger.info("Migration completed successfully")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
