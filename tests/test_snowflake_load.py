import os
import snowflake.connector
from dotenv import load_dotenv

def validate_data_loading():
    """Validate that data was loaded correctly."""
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

        # Check total row count
        cursor.execute("SELECT COUNT(*) FROM SC_RAW_DATA.raw_data")
        total_count = cursor.fetchone()[0]
        print(f"✅ Total records in RAW_DATA.raw_data: {total_count}")

        # Check data by source
        cursor.execute("""
        SELECT source_system, COUNT(*)
        FROM SC_RAW_DATA.raw_data
        GROUP BY source_system
        """)

        for source, count in cursor.fetchall():
            print(f"   {source}: {count} records")

        # Sample data validation
        cursor.execute("SELECT * FROM SC_RAW_DATA.raw_data LIMIT 3")
        sample_data = cursor.fetchall()

        print("\n📊 Sample data:")
        for row in sample_data:
            print(f"   {row}")

        return True

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False
    finally:
        conn.close()

def test_validate_data_loading():
    print("🚀 Starting test: validate_data_loading")
    result = validate_data_loading()
    if result:
        print("✅ Test passed: Data loaded and validated successfully.")
    else:
        print("❌ Test failed: Data validation unsuccessful.")
    assert result is True

def validate_data_loading_postgre():
    """Validate that data was loaded correctly into raw_data_postgre."""
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

        # Check total row count
        cursor.execute("SELECT COUNT(*) FROM SC_RAW_DATA.raw_data_postgre")
        total_count = cursor.fetchone()[0]
        print(f"✅ Total records in SC_RAW_DATA.raw_data_postgre: {total_count}")

        # Check if source_system column exists
        cursor.execute("""
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'SC_RAW_DATA'
              AND TABLE_NAME = 'RAW_DATA_POSTGRE'
              AND COLUMN_NAME = 'SOURCE_SYSTEM'
        """)
        has_source_system = cursor.fetchone() is not None

        if has_source_system:
            cursor.execute("""
            SELECT source_system, COUNT(*)
            FROM SC_RAW_DATA.raw_data_postgre
            GROUP BY source_system
            """)
            for source, count in cursor.fetchall():
                print(f"   {source}: {count} records")
        else:
            print("ℹ️ 'source_system' column not found in SC_RAW_DATA.raw_data_postgre. Skipping group by source_system.")

        # Sample data validation
        cursor.execute("SELECT * FROM SC_RAW_DATA.raw_data_postgre LIMIT 3")
        sample_data = cursor.fetchall()

        print("\n📊 Sample data from raw_data_postgre:")
        for row in sample_data:
            print(f"   {row}")

        return True

    except Exception as e:
        print(f"❌ Validation failed for raw_data_postgre: {e}")
        return False
    finally:
        conn.close()

def test_validate_data_loading_postgre():
    print("🚀 Starting test: validate_data_loading_postgre")
    result = validate_data_loading_postgre()
    if result:
        print("✅ Test passed: Data loaded and validated successfully for raw_data_postgre.")
    else:
        print("❌ Test failed: Data validation unsuccessful for raw_data_postgre.")
    assert result is True

if __name__ == "__main__":
    test_validate_data_loading()
    test_validate_data_loading_postgre()