-- Database initialization script for MarketMindAI
-- This script runs when PostgreSQL container starts for the first time

-- Create database if not exists
CREATE DATABASE marketmindai;

-- Create user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'marketmindai') THEN
        CREATE USER marketmindai WITH PASSWORD 'marketmindai123';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE marketmindai TO marketmindai;

-- Connect to the database
\c marketmindai;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO marketmindai;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO marketmindai;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO marketmindai;