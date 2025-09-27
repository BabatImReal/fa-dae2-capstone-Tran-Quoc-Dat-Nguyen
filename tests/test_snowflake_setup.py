import snowflake.connector
from dotenv import load_dotenv
import os

def verify_snowflake_setup():
    """Verify all required Snowflake objects exist."""
    load_dotenv()

    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        authenticator="SNOWFLAKE_JWT",
        private_key_file=os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PATH"),
        private_key_file_pwd=os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PWD"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        role=os.getenv("SNOWFLAKE_ROLE"),
    )

    try:
        cursor = conn.cursor()

        # Check warehouse
        cursor.execute("SHOW WAREHOUSES LIKE 'WH_T22'")
        if not cursor.fetchall():
            print("❌ Warehouse WH_T22 not found")
            return False

        # Check database
        cursor.execute("SHOW DATABASES LIKE 'DB_T22'")
        if not cursor.fetchall():
            print("❌ Database DB_T22 not found")
            return False

        # Check schemas
        cursor.execute("SHOW SCHEMAS IN DATABASE DB_T22")
        schemas = [row[1] for row in cursor.fetchall()]
        required_schemas = ['SC_RAW_DATA', 'SC_STAGING', 'SC_ANALYTICS']

        for schema in required_schemas:
            if schema not in schemas:
                print(f"❌ Schema {schema} not found")
                return False

        # Check stages
        cursor.execute("SHOW STAGES IN SCHEMA SC_RAW_DATA")
        stages = [row[1] for row in cursor.fetchall()]
        required_stages = ['CSV_STAGE', 'JSON_STAGE']

        for stage in required_stages:
            if stage not in stages:
                print(f"❌ Stage {stage} not found")
                return False

        print("✅ All Snowflake objects verified!")
        return True

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    verify_snowflake_setup()