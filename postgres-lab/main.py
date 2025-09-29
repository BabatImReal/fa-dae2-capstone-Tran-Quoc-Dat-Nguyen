#!/usr/bin/env python3
"""
Week 02 Lab: Simple PostgreSQL Connection and Data Landing
This script demonstrates basic database connectivity and data insertion.
"""

import sys
from pathlib import Path

# Add the scripts directory to the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.database.connection_test import test_connection
from scripts.database.crud_demo import demonstrate_crud
from scripts.ingestion.ingest_to_postgre import insert_music_transactions
import json

def main():
    """Main function to run the lab exercises."""
    print("🚀 Week 02 Lab: PostgreSQL Connection and Data Landing")
    print("=" * 60)

    # Test database connection
    print("\n1️⃣ Testing Database Connection...")
    if not test_connection():
        print("❌ Database connection failed. Please check your Docker setup.")
        return False

    # # Demonstrate basic CRUD operations
    # print("\n2️⃣ Demonstrating Basic CRUD Operations...")
    # if not demonstrate_crud():
    #     print("❌ CRUD operations failed.")
    #     return False

    # Load and insert fake music transactions
    print("\n3️⃣ Loading and Inserting Fake Music Transactions...")
    data_dir = Path(__file__).parent.parent / "data" / "external"
    json_files = sorted(data_dir.glob("fake_music_transactions_*.json"), reverse=True)
    if not json_files:
        print(f"❌ No timestamped data files found in: {data_dir}")
        return False

    data_path = json_files[0]  # Use the latest file
    print(f"Using data file: {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        music_transactions = json.load(f)

    if not insert_music_transactions(music_transactions):
        print("❌ Failed to insert music transactions into PostgreSQL.")
        return False

    print("\n✅ Lab completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)