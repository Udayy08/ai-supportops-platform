-- PostgreSQL initialization script
-- Runs once when the postgres container is first created.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For full-text trigram search

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE supportops TO supportops;
