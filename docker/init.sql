-- Initialize trading bot database
-- This script is run when the PostgreSQL container starts

-- Create database if it doesn't exist
SELECT 'CREATE DATABASE trading_bot'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'trading_bot')\gexec

-- Connect to the trading_bot database
\c trading_bot;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for better performance
-- These will be created by Alembic migrations, but we can add some initial ones here

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE trading_bot TO trading_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;
