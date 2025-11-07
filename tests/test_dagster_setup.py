"""
Quick test to verify dlt and Dagster setup.
Run this before starting the full orchestrator.
"""

import sys
from pathlib import Path

# Test 1: Import checks
print("=" * 60)
print("🧪 Testing imports...")
print("=" * 60)

try:
    import dlt
    print(f"✅ dlt version: {dlt.__version__}")
except ImportError as e:
    print(f"❌ dlt import failed: {e}")
    sys.exit(1)

try:
    import dagster
    print(f"✅ dagster version: {dagster.__version__}")
except ImportError as e:
    print(f"❌ dagster import failed: {e}")
    sys.exit(1)

try:
    from dagster_dbt import DbtCliResource
    print("✅ dagster-dbt available")
except ImportError as e:
    print(f"❌ dagster-dbt import failed: {e}")

try:
    from dlt.sources.sql_database import sql_table
    print("✅ dlt.sources.sql_database available")
except ImportError as e:
    print(f"❌ dlt sql_database import failed: {e}")
    sys.exit(1)

try:
    import psycopg
    print(f"✅ psycopg available")
except ImportError as e:
    print(f"❌ psycopg import failed: {e}")

try:
    import snowflake.connector
    print(f"✅ snowflake-connector available")
except ImportError as e:
    print(f"❌ snowflake-connector import failed: {e}")

# Test 2: Environment variables
print("\n" + "=" * 60)
print("🔐 Testing environment variables...")
print("=" * 60)

import os
from dotenv import load_dotenv

load_dotenv()

required_vars = [
    "POSTGRES_HOST",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "SNOWFLAKE_ACCOUNT",
    "SNOWFLAKE_USER",
    "SNOWFLAKE_WAREHOUSE",
    "SNOWFLAKE_DATABASE",
]

missing_vars = []
for var in required_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        display_value = value if len(value) < 20 else value[:10] + "..."
        print(f"✅ {var}: {display_value}")
    else:
        print(f"❌ {var}: NOT SET")
        missing_vars.append(var)

if missing_vars:
    print(f"\n⚠️  Warning: {len(missing_vars)} required variables not set")
else:
    print("\n✅ All required environment variables are set")

# Test 3: Config file
print("\n" + "=" * 60)
print("📄 Testing config.yaml...")
print("=" * 60)

import yaml

project_root = Path(__file__).resolve().parents[1]
config_path = project_root / "config.yaml"

if config_path.exists():
    print(f"✅ Found config.yaml at: {config_path}")
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        print(f"✅ Config loaded successfully")
        print(f"   - PostgreSQL schema: {config.get('postgresql', {}).get('schema')}")
        print(f"   - PostgreSQL table: {config.get('postgresql', {}).get('table')}")
        print(f"   - Data directory: {config.get('paths', {}).get('data_dir')}")
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
else:
    print(f"❌ Config file not found at: {config_path}")

# Test 4: Database connectivity (optional)
print("\n" + "=" * 60)
print("🔌 Testing database connections...")
print("=" * 60)

# PostgreSQL
try:
    import psycopg
    conn_string = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB')}"
    with psycopg.connect(conn_string) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()[0]
            print(f"✅ PostgreSQL connected: {version.split(',')[0]}")
except Exception as e:
    print(f"⚠️  PostgreSQL connection failed: {e}")
    print("   (This is OK if PostgreSQL is not running)")

# Snowflake
try:
    import snowflake.connector
    
    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        authenticator="SNOWFLAKE_JWT",
        private_key_file=os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PATH"),
        private_key_file_pwd=os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PWD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
    )
    cur = conn.cursor()
    cur.execute("SELECT CURRENT_VERSION()")
    version = cur.fetchone()[0]
    cur.close()
    conn.close()
    print(f"✅ Snowflake connected: version {version}")
except Exception as e:
    print(f"⚠️  Snowflake connection failed: {e}")
    print("   (Check your credentials and private key)")

# Summary
print("\n" + "=" * 60)
print("📋 Test Summary")
print("=" * 60)
print("✅ All required packages are installed")
print("✅ dlt is ready to use")
print("✅ Dagster is ready to use")
print("\n🚀 Next steps:")
print("   1. Ensure PostgreSQL is running: docker-compose up -d")
print("   2. Run the standalone dlt script:")
print("      python scripts/ingestion/dlt_postgres_to_snowflake.py")
print("   3. Start Dagster UI:")
print("      cd dagster-orchestrator && dagster dev")
print("=" * 60)
