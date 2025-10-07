-- Simple PostgreSQL initialization for Week 02 Lab
-- This creates a basic staging table for landing data

-- Create staging schema
CREATE SCHEMA IF NOT EXISTS staging;


-- Create hospital_transactions table for hospital transaction fake data
CREATE TABLE IF NOT EXISTS staging.hospital_transactions (
    transaction_id UUID PRIMARY KEY,
    patient_id UUID,
    admission_id UUID,
    department VARCHAR(100),
    doctor VARCHAR(100),
    service VARCHAR(255),
    cost NUMERIC(10,2),
    payment_method VARCHAR(50),
    transaction_time TIMESTAMP,
    status VARCHAR(20),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant permissions (user already exists from Docker environment)
GRANT ALL PRIVILEGES ON SCHEMA staging TO staging_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA staging TO staging_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA staging TO staging_user;