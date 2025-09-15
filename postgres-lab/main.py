#!/usr/bin/env python3
"""
Week 02 Lab: Simple PostgreSQL Connection and Data Landing
This script demonstrates basic database connectivity and data insertion.
"""

import sys
from pathlib import Path

# Add the scripts directory to the path
sys.path.append(str(Path(__file__).parent / "scripts" / "database"))

from scripts.database.connection_test import test_connection
from scripts.database.crud_demo import demonstrate_crud

def main():
    """Main function to run the lab exercises."""
    print("🚀 Week 02 Lab: PostgreSQL Connection and Data Landing")
    print("=" * 60)

    # Test database connection
    print("\n1️⃣ Testing Database Connection...")
    if not test_connection():
        print("❌ Database connection failed. Please check your Docker setup.")
        return False

    # Demonstrate basic CRUD operations
    print("\n2️⃣ Demonstrating Basic CRUD Operations...")
    if not demonstrate_crud():
        print("❌ CRUD operations failed.")
        return False

    print("\n✅ Lab completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)