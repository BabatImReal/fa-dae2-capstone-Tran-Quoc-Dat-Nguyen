#!/usr/bin/env python3
"""
Connection Test Suite
Tests connectivity to all database systems used in the project:
- PostgreSQL (staging database)
- Snowflake (data warehouse)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to the path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

# Load environment variables
load_dotenv()


def test_postgresql_connection():
    """Test PostgreSQL database connection."""
    print("\n🐘 Testing PostgreSQL Connection...")
    print("-" * 40)

    try:
        import psycopg

        # Connection parameters
        params = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "dbname": os.getenv("POSTGRES_DB", "staging_db"),
            "user": os.getenv("POSTGRES_USER", "staging_user"),
            "password": os.getenv("POSTGRES_PASSWORD"),
        }

        print(
            f"📡 Connecting to: {params['user']}@{params['host']}:{params['port']}/{params['dbname']}"
        )

        # Test connection
        with psycopg.connect(**params) as conn:
            with conn.cursor() as cur:
                # Get PostgreSQL version
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print("✅ Connection successful!")
                print(f"📊 Version: {version}")

                # Test staging schema
                cur.execute(
                    "SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'staging';"
                )
                schema_exists = cur.fetchone()
                if schema_exists:
                    print("✅ Staging schema exists")
                else:
                    print("❌ Staging schema not found")
                    return False

                # Test music_transactions table
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'staging' AND table_name = 'music_transactions';
                """)
                table_exists = cur.fetchone()
                if table_exists:
                    cur.execute("SELECT COUNT(*) FROM staging.music_transactions;")
                    record_count = cur.fetchone()[0]
                    print(
                        f"✅ music_transactions table exists with {record_count} records"
                    )
                else:
                    print("❌ music_transactions table not found")
                    return False

        return True

    except ImportError:
        print("❌ psycopg module not found. Install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False


def test_snowflake_connection():
    """Test Snowflake data warehouse connection."""
    print("\n❄️ Testing Snowflake Connection...")
    print("-" * 40)

    try:
        import snowflake.connector

        # Connection parameters
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

        # Check for required environment variables
        missing_vars = [key for key, value in connection_params.items() if not value]
        if missing_vars:
            print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
            return False

        print(
            f"📡 Connecting to: {connection_params['user']}@{connection_params['account']}"
        )
        print(
            f"🏢 Database: {connection_params['database']}.{connection_params['schema']}"
        )

        # Test connection
        with snowflake.connector.connect(**connection_params) as conn:
            with conn.cursor() as cur:
                # Get Snowflake version
                cur.execute("SELECT CURRENT_VERSION();")
                version = cur.fetchone()[0]
                print("✅ Connection successful!")
                print(f"📊 Version: {version}")

                # Test current database and schema
                cur.execute("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA();")
                db_schema = cur.fetchone()
                print(f"📂 Current context: {db_schema[0]}.{db_schema[1]}")

                # Test warehouse
                cur.execute("SELECT CURRENT_WAREHOUSE();")
                warehouse = cur.fetchone()[0]
                print(f"🏭 Current warehouse: {warehouse}")

                # Test SC_RAW_DATA schema
                try:
                    cur.execute("USE SCHEMA SC_RAW_DATA;")
                    print("✅ SC_RAW_DATA schema accessible")

                    # Test raw_data_postgre table
                    try:
                        cur.execute(
                            "SELECT COUNT(*) FROM SC_RAW_DATA.RAW_DATA_POSTGRE;"
                        )
                        record_count = cur.fetchone()[0]
                        print(
                            f"✅ RAW_DATA_POSTGRE table exists with {record_count} records"
                        )
                    except Exception as table_error:
                        print(
                            f"❌ RAW_DATA_POSTGRE table not accessible: {table_error}"
                        )
                        return False

                except Exception as schema_error:
                    print(f"❌ SC_RAW_DATA schema not accessible: {schema_error}")
                    return False

        return True

    except ImportError:
        print(
            "❌ snowflake-connector-python module not found. Install with: pip install snowflake-connector-python"
        )
        return False
    except Exception as e:
        print(f"❌ Snowflake connection failed: {e}")
        return False


def test_environment_variables():
    """Test that all required environment variables are set."""
    print("\n🔧 Testing Environment Variables...")
    print("-" * 40)

    required_vars = {
        "PostgreSQL": [
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
        ],
        "Snowflake": [
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_PRIVATE_KEY_FILE_PATH",
            "SNOWFLAKE_PRIVATE_KEY_FILE_PWD",
            "SNOWFLAKE_WAREHOUSE",
            "SNOWFLAKE_DATABASE",
            "SNOWFLAKE_SCHEMA",
            "SNOWFLAKE_ROLE",
        ],
    }

    all_good = True

    for system, vars_list in required_vars.items():
        print(f"\n{system} Environment Variables:")
        for var in vars_list:
            value = os.getenv(var)
            if value:
                # Mask sensitive values
                if "PASSWORD" in var or "PWD" in var:
                    display_value = "*" * len(value)
                elif "KEY" in var:
                    display_value = (
                        f"{value[:10]}...{value[-10:]}"
                        if len(value) > 20
                        else "*" * len(value)
                    )
                else:
                    display_value = value
                print(f"  ✅ {var}: {display_value}")
            else:
                print(f"  ❌ {var}: Not set")
                all_good = False

    return all_good


def main():
    """Run all connection tests."""
    print("🧪 Database Connection Test Suite")
    print("=" * 50)

    # Test environment variables
    env_ok = test_environment_variables()

    # Test PostgreSQL connection
    pg_ok = test_postgresql_connection()

    # Test Snowflake connection
    sf_ok = test_snowflake_connection()

    # Summary
    print("\n📋 Test Summary")
    print("=" * 50)
    print(f"Environment Variables: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"PostgreSQL Connection: {'✅ PASS' if pg_ok else '❌ FAIL'}")
    print(f"Snowflake Connection:  {'✅ PASS' if sf_ok else '❌ FAIL'}")

    all_tests_passed = env_ok and pg_ok and sf_ok

    if all_tests_passed:
        print("\n🎉 All connection tests passed!")
        print("💾 Your data pipeline is ready to use!")
    else:
        print("\n❌ Some tests failed. Please check your configuration.")
        print("📋 Common fixes:")
        print("  - Ensure Docker containers are running (PostgreSQL)")
        print("  - Check .env file for correct credentials")
        print("  - Verify Snowflake private key file path and permissions")

    return all_tests_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
