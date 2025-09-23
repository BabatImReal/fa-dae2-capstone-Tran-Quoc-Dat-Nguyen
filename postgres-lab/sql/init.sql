-- Simple PostgreSQL initialization for Week 02 Lab
-- This creates a basic staging table for landing data

-- Create staging schema
CREATE SCHEMA IF NOT EXISTS staging;

-- Create music_transactions table with music event structure
CREATE TABLE IF NOT EXISTS staging.music_transactions (
    event_id UUID PRIMARY KEY,
    user_id UUID,
    session_id UUID,
    song_id UUID,
    song_title VARCHAR(255),
    artist VARCHAR(255),
    album VARCHAR(255),
    genre VARCHAR(50),
    duration_seconds INTEGER,
    position_seconds INTEGER,
    event_action VARCHAR(50),
    device_type VARCHAR(50),
    platform VARCHAR(50),
    timestamp TIMESTAMP,
    user_premium BOOLEAN,
    ingested_at TIMESTAMP
);

-- Grant permissions (user already exists from Docker environment)
GRANT ALL PRIVILEGES ON SCHEMA staging TO staging_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO staging_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA staging TO staging_user;