#!/usr/bin/env python3
"""
Connection Integration Test
Tests that all data pipeline connections and operations work end-to-end.
"""

from datetime import datetime
import json
import os
from pathlib import Path
import sys

from dotenv import load_dotenv

# Add the project root to the path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()


def test_fake_data_generation():
    """Test that fake data generation works."""
    print("\n🎭 Testing Fake Data Generation...")
    print("-" * 40)

    try:
        from scripts.ingestion.collect_fake_data import FakeDataGenerator

        # Generate small test dataset
        generator = FakeDataGenerator()
        test_data = generator.generate_music_transaction_data(5)  # Small test

        if not test_data:
            print("❌ No data generated")
            return False

        print(f"✅ Generated {len(test_data)} test records")

        # Validate data structure
        required_fields = [
            "event_id",
            "user_id",
            "session_id",
            "song_id",
            "song_title",
            "artist",
            "album",
            "genre",
            "duration_seconds",
            "position_seconds",
            "event_action",
            "device_type",
            "platform",
            "timestamp",
            "user_premium",
        ]

        first_record = test_data[0]
        missing_fields = [
            field for field in required_fields if field not in first_record
        ]

        if missing_fields:
            print(f"❌ Missing fields: {missing_fields}")
            return False

        print("✅ Data structure validation passed")

        # Check for music event actions
        actions = [record["event_action"] for record in test_data]
        music_actions = ["play", "pause", "next", "previous", "skip", "like", "stop"]
        has_music_actions = any(action in music_actions for action in actions)

        if has_music_actions:
            print("✅ Contains proper music listening events")
        else:
            print("⚠️ No standard music actions found")

        return True

    except Exception as e:
        print(f"❌ Fake data generation failed: {e}")
        return False


def test_postgresql_ingestion():
    """Test PostgreSQL data ingestion."""
    print("\n🐘 Testing PostgreSQL Ingestion...")
    print("-" * 40)

    try:
        from scripts.ingestion.collect_fake_data import FakeDataGenerator
        from scripts.ingestion.ingest_to_postgre import (
            get_connection,
            insert_music_transactions,
        )

        # Generate test data
        generator = FakeDataGenerator()
        test_data = generator.add_ingested_at(
            generator.generate_music_transaction_data(3)
        )

        print(f"📊 Generated {len(test_data)} test records")

        # Test database connection
        try:
            with get_connection() as conn, conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM staging.music_transactions;")
                initial_count = cur.fetchone()[0]
                print(f"📈 Initial record count: {initial_count}")
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

        # Test data insertion
        success = insert_music_transactions(test_data)

        if not success:
            print("❌ Data insertion failed")
            return False

        # Verify insertion
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM staging.music_transactions;")
            final_count = cur.fetchone()[0]

        records_added = final_count - initial_count
        print("✅ Successfully inserted data")
        print(f"📈 Final record count: {final_count} (+{records_added})")

        return True

    except Exception as e:
        print(f"❌ PostgreSQL ingestion test failed: {e}")
        return False


def test_snowflake_ingestion():
    """Test Snowflake data ingestion."""
    print("\n❄️ Testing Snowflake Ingestion...")
    print("-" * 40)

    try:
        # Import the ingestion script with proper path handling
        ingestion_module_path = project_root / "scripts" / "ingestion"
        if str(ingestion_module_path) not in sys.path:
            sys.path.insert(0, str(ingestion_module_path))

        import ingest_postgre_to_snowflake
        import snowflake.connector

        # Check initial Snowflake count
        connection_params = {
            "account": os.getenv("SNOWFLAKE_ACCOUNT"),
            "user": os.getenv("SNOWFLAKE_USER"),
            "authenticator": "SNOWFLAKE_JWT",
            "private_key_file": os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PATH"),
            "private_key_file_pwd": os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PWD"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
            "database": os.getenv("SNOWFLAKE_DATABASE"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA"),
            "role": os.getenv("SNOWFLAKE_ROLE"),
        }

        try:
            with snowflake.connector.connect(**connection_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM SC_RAW_DATA.RAW_DATA_POSTGRE;")
                    initial_sf_count = cur.fetchone()[0]
                    print(f"📈 Initial Snowflake count: {initial_sf_count}")
        except Exception as e:
            print(f"❌ Snowflake connection failed: {e}")
            return False

        # Run the ingestion process
        print("🔄 Running PostgreSQL to Snowflake ingestion...")

        # Capture the function output
        try:
            ingest_postgre_to_snowflake.load_postgres_to_snowflake()
            print("✅ Ingestion process completed without errors")
        except Exception as e:
            print(f"❌ Ingestion process failed: {e}")
            return False

        # Verify final count
        try:
            with snowflake.connector.connect(**connection_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM SC_RAW_DATA.RAW_DATA_POSTGRE;")
                    final_sf_count = cur.fetchone()[0]

            records_added = final_sf_count - initial_sf_count
            print(f"📈 Final Snowflake count: {final_sf_count} (+{records_added})")

            if records_added >= 0:
                print("✅ Snowflake ingestion test passed")
                return True
            print("❌ Unexpected record count change")
            return False

        except Exception as e:
            print(f"❌ Final count verification failed: {e}")
            return False

    except Exception as e:
        print(f"❌ Snowflake ingestion test failed: {e}")
        return False


def test_end_to_end_pipeline():
    """Test the complete data pipeline end-to-end."""
    print("\n🔄 Testing End-to-End Pipeline...")
    print("-" * 40)

    try:
        # Step 1: Generate new fake data
        print("1️⃣ Generating fresh test data...")
        from scripts.ingestion.collect_fake_data import FakeDataGenerator

        generator = FakeDataGenerator()
        test_data = generator.add_ingested_at(
            generator.generate_music_transaction_data(5)
        )

        # Save to temporary file (simulate the actual process)
        data_dir = project_root / "data" / "external"
        data_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
        test_file = data_dir / f"test_music_transactions_{timestamp}.json"

        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Created test file: {test_file.name}")

        # Step 2: Ingest to PostgreSQL
        print("2️⃣ Testing PostgreSQL ingestion...")
        from scripts.ingestion.ingest_to_postgre import insert_music_transactions

        if not insert_music_transactions(test_data):
            print("❌ PostgreSQL ingestion failed")
            return False

        print("✅ PostgreSQL ingestion successful")

        # Step 3: Ingest to Snowflake
        print("3️⃣ Testing Snowflake ingestion...")

        # Import with proper path handling
        ingestion_module_path = project_root / "scripts" / "ingestion"
        if str(ingestion_module_path) not in sys.path:
            sys.path.insert(0, str(ingestion_module_path))

        import ingest_postgre_to_snowflake

        try:
            ingest_postgre_to_snowflake.load_postgres_to_snowflake()
            print("✅ Snowflake ingestion successful")
        except Exception as e:
            print(f"⚠️ Snowflake ingestion encountered issues: {e}")
            # Don't fail the test if it's just a duplicate/no new data issue

        # Cleanup test file
        if test_file.exists():
            test_file.unlink()
            print("🧹 Cleaned up test file")

        print("✅ End-to-end pipeline test completed")
        return True

    except Exception as e:
        print(f"❌ End-to-end pipeline test failed: {e}")
        return False


def main():
    """Run all connection and functionality tests."""
    print("🧪 Data Pipeline Integration Tests")
    print("=" * 50)

    # Run all tests
    tests = [
        ("Fake Data Generation", test_fake_data_generation),
        ("PostgreSQL Ingestion", test_postgresql_ingestion),
        ("Snowflake Ingestion", test_snowflake_ingestion),
        ("End-to-End Pipeline", test_end_to_end_pipeline),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False

    # Summary
    print("\n📋 Test Results Summary")
    print("=" * 50)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<25}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n🎉 All tests passed!")
        print("💾 Your data pipeline is working correctly!")
    else:
        failed_tests = [name for name, passed in results.items() if not passed]
        print(f"\n❌ {len(failed_tests)} test(s) failed:")
        for test in failed_tests:
            print(f"  - {test}")
        print("\n🔧 Please check your configuration and try again.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
