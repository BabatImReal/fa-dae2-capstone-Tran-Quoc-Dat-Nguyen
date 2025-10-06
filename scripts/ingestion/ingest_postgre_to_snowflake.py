import os
import re
import psycopg
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv

def sanitize_identifier(identifier):
    """Sanitize SQL identifiers to prevent injection."""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$', identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier}")
    return identifier

def load_postgres_to_snowflake():
    """Incrementally extract data from PostgreSQL and load into Snowflake (SC_RAW_DATA.raw_data_postgre)."""
    load_dotenv()

    # -------------------------------
    # Connect to Snowflake first to get latest ingested_at
    # -------------------------------
    sf_conn = snowflake.connector.connect(
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

    cur = sf_conn.cursor()
    # Use row count comparison instead of timestamp to avoid conversion issues
    try:
        # Sanitize table name
        table_name = sanitize_identifier("SC_RAW_DATA.RAW_DATA_POSTGRE")
        
        # Get count of records in Snowflake
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        sf_row_count = cur.fetchone()[0]
        print(f"📊 Snowflake table has {sf_row_count} records")

    except snowflake.connector.errors.ProgrammingError as e:
        if "does not exist" in str(e).lower():
            print("⚠️ Table SC_RAW_DATA.RAW_DATA_POSTGRE does not exist yet")
            sf_row_count = 0
        else:
            print(f"⚠️ Error querying Snowflake table: {e}")
            sf_row_count = 0
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        sf_row_count = 0
    cur.close()

    # -------------------------------
    # Connect to PostgreSQL
    # -------------------------------
    pg_conn = psycopg.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

    # Build query to get all data from PostgreSQL (we'll filter after loading)
    query = """
        SELECT 
            event_id,
            user_id,
            session_id,
            song_id,
            song_title,
            artist,
            album,
            genre,
            duration_seconds,
            position_seconds,
            event_action,
            device_type,
            platform,
            "timestamp" AS event_timestamp,   -- reserved word
            user_premium,
            ingested_at
        FROM staging.music_transactions
        ORDER BY ingested_at
    """

    df = pd.read_sql_query(query, pg_conn)
    pg_conn.close()

    print(f"📊 Total records in PostgreSQL: {len(df)}")
    if not df.empty:
        print(
            f"📅 PostgreSQL data range: {df['ingested_at'].min()} to {df['ingested_at'].max()}"
        )

    if df.empty:
        print("👌 No new data to ingest")
        sf_conn.close()
        return

    # -------------------------------
    # Transform: type conversions
    # -------------------------------
    uuid_cols = ["event_id", "user_id", "session_id", "song_id"]
    for col in uuid_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)

    # Convert timestamp columns to datetime (keep as datetime, do NOT format as string)
    ts_cols = ["event_timestamp", "ingested_at"]
    for col in ts_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Simple incremental logic: only load records beyond what Snowflake already has
    pg_total_records = len(df)
    if sf_row_count > 0 and sf_row_count < pg_total_records:
        # Skip the first sf_row_count records (already in Snowflake)
        df = df.iloc[sf_row_count:].copy().reset_index(drop=True)
        print(f"🔍 Incremental load: skipping first {sf_row_count} records")
        print(
            f"📊 Loading records {sf_row_count + 1} to {pg_total_records} ({len(df)} new records)"
        )
    elif sf_row_count >= pg_total_records:
        print(
            f"👌 Snowflake already has {sf_row_count} records, PostgreSQL has {pg_total_records}. Nothing to load."
        )
        sf_conn.close()
        return
    else:
        print(
            f"📋 Full load: Snowflake has {sf_row_count} records, loading all {pg_total_records} from PostgreSQL"
        )

    # Rename columns to uppercase for Snowflake compatibility
    df.columns = [c.upper() for c in df.columns]

    if df.empty:
        print("👌 No new data to ingest")
        sf_conn.close()
        return

    print(f"✅ Processing {len(df)} new records for Snowflake load")

    # -------------------------------
    # Load into Snowflake
    # -------------------------------
    try:
        success, nchunks, nrows, _ = write_pandas(
            sf_conn,
            df,
            "RAW_DATA_POSTGRE",
            schema="SC_RAW_DATA",
        )
        print(
            f"✅ Loaded {nrows} new records into Snowflake table SC_RAW_DATA.raw_data_postgre"
        )

    except Exception as e:
        print(f"❌ Loading failed: {e}")
    finally:
        sf_conn.close()


if __name__ == "__main__":
    load_postgres_to_snowflake()