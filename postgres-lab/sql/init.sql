-- Simple PostgreSQL initialization for Week 02 Lab
-- This creates a basic staging table for landing data

-- Create staging schema
CREATE SCHEMA IF NOT EXISTS staging;


-- Create user_events table for user event fake data
CREATE TABLE IF NOT EXISTS staging.user_events (
    event_id UUID PRIMARY KEY,
    user_id UUID,
    session_id UUID,
    event_type VARCHAR(50),
    event_timestamp TIMESTAMP,
    user_agent TEXT,
    ip_address VARCHAR(45),
    page_url TEXT,
    page_title TEXT,
    referrer TEXT,
    product_id UUID,
    product_name TEXT,
    category VARCHAR(100),
    price NUMERIC(10,2),
    quantity INTEGER,
    search_query TEXT,
    results_count INTEGER,
    filters_applied BOOLEAN,
    checkout_step VARCHAR(50),
    cart_value NUMERIC(10,2),
    item_count INTEGER,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions (user already exists from Docker environment)
GRANT ALL PRIVILEGES ON SCHEMA staging TO staging_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO staging_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA staging TO staging_user;