#!/usr/bin/env python3
"""
Simple CRUD operations demo for Week 02 Lab
"""

import os
import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_connection():
    """Get database connection."""
    params = {
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }
    return psycopg.connect(**params)

def demonstrate_crud():
    """Demonstrate basic CRUD operations."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                print("📝 Creating sample data...")

                # CREATE - Insert sample data
                sample_data = [
                    ("Sample JSON data", "users.json"),
                    ("Sample CSV data", "products.csv"),
                    ("Sample log data", "app.log"),
                ]

                for content, filename in sample_data:
                    cur.execute(
                        "INSERT INTO staging.raw_data (data_content, file_name) VALUES (%s, %s) RETURNING id",
                        (content, filename)
                    )
                    record_id = cur.fetchone()[0]
                    print(f"   ✅ Created record {record_id}: {filename}")

                # READ, UPDATE, DELETE operations...
                return True
    except Exception as e:
        print(f"❌ CRUD operations failed: {str(e)}")
        return False