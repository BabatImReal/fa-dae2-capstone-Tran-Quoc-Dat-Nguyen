import os
import psycopg
import pandas as pd
import snowflake.connector
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv


def load_postgres_to_snowflake():
    """Extract data from PostgreSQL and bulk load into Snowflake (SC_RAW_DATA.raw_data_postgre)."""
    load_dotenv()

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
            "timestamp" AS event_timestamp,   -- reserved word, alias to event_timestamp
            user_premium,
            ingested_at
        FROM staging.music_transactions
    """
    df = pd.read_sql_query(query, pg_conn)
    pg_conn.close()

    print(f"✅ Extracted {len(df)} records from PostgreSQL")

    # -------------------------------
    # Transform: convert types for Snowflake compatibility
    # -------------------------------
    # UUIDs → strings
    uuid_cols = ["event_id", "user_id", "session_id", "song_id"]
    for col in uuid_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)

    # Timestamps → strings (Snowflake auto-parses them as TIMESTAMP_NTZ)
    ts_cols = ["event_timestamp", "ingested_at"]
    for col in ts_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.strftime("%Y-%m-%d %H:%M:%S")
    df.columns = [c.upper() for c in df.columns]

    # -------------------------------
    # Connect to Snowflake
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

    try:
        # -------------------------------
        # Load into Snowflake
        # -------------------------------
        success, nchunks, nrows, _ = write_pandas(
            sf_conn,
            df,
            "RAW_DATA_POSTGRE",
            schema="SC_RAW_DATA",
        )
        print(f"✅ Loaded {nrows} records into Snowflake table SC_RAW_DATA.raw_data_postgre")

    except Exception as e:
        print(f"❌ Loading failed: {e}")
    finally:
        sf_conn.close()


if __name__ == "__main__":
    load_postgres_to_snowflake()
