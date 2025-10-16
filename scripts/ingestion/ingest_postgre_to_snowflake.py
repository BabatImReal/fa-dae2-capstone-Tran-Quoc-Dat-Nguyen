# Standard library imports
import logging
import os
import re

# Third-party imports
import pandas as pd
import psycopg
import snowflake.connector
import yaml
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

# ------------------------------------------------------------
# LOGGING SETUP
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------
# CONFIG LOADER
# ------------------------------------------------------------
def load_config():
    """Load configuration from YAML file."""
    with open("config.yaml", 'r') as file:
        return yaml.safe_load(file)

config = load_config()

SNOWFLAKE_POSTGRE_TABLE = config['snowflake']['postgre_table']
POSTGRES_SCHEMA = config['postgresql']['schema']
POSTGRES_TABLE = config['postgresql']['table']

# ------------------------------------------------------------
# SQL IDENTIFIER SANITIZER
# ------------------------------------------------------------
def sanitize_identifier(identifier):
    """Sanitize SQL identifiers to prevent injection."""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$', identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier}")
    return identifier

# ------------------------------------------------------------
# MAIN PIPELINE
# ------------------------------------------------------------
def load_postgres_to_snowflake():
    """Incrementally extract data from PostgreSQL and load into Snowflake."""
    load_dotenv()

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

    cur = sf_conn.cursor()
    try:
        table_name = sanitize_identifier(SNOWFLAKE_POSTGRE_TABLE)
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        sf_row_count = cur.fetchone()[0]
        logger.info(f"📊 Snowflake table has {sf_row_count} records")
    except snowflake.connector.errors.ProgrammingError as e:
        if "does not exist" in str(e).lower():
            logger.warning(f"Table {SNOWFLAKE_POSTGRE_TABLE} does not exist yet")
            sf_row_count = 0
        else:
            logger.error(f"Error querying Snowflake table: {e}")
            sf_row_count = 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
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

    query = f"""
        SELECT 
            event_id,
            user_id,
            session_id,
            event_type,
            event_timestamp,
            user_agent,
            ip_address,
            page_url,
            page_title,
            referrer,
            product_id,
            product_name,
            category,
            price,
            quantity,
            search_query,
            results_count,
            filters_applied,
            checkout_step,
            cart_value,
            item_count,
            ingested_at
        FROM {POSTGRES_SCHEMA}.{POSTGRES_TABLE}
        ORDER BY ingested_at
    """

    df = pd.read_sql_query(query, pg_conn)
    pg_conn.close()

    logger.info(f"📊 Total records in PostgreSQL: {len(df)}")
    if not df.empty:
        logger.info(
            f"📅 PostgreSQL data range: {df['ingested_at'].min()} → {df['ingested_at'].max()}"
        )

    if df.empty:
        logger.info("👌 No new data to ingest")
        sf_conn.close()
        return

    # -------------------------------
    # Transform: type conversions
    # -------------------------------
    uuid_cols = ["event_id", "user_id", "session_id", "product_id"]
    for col in uuid_cols:
        if col in df.columns:
            df[col] = df[col].astype(str)

    # Convert timestamp columns to strings for Snowflake compatibility
    ts_cols = ["event_timestamp", "ingested_at"]
    for col in ts_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            # ✅ SAFE FIX: convert to ISO string format
            df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')

    # -------------------------------
    # Incremental load logic
    # -------------------------------
    pg_total_records = len(df)
    if sf_row_count > 0 and sf_row_count < pg_total_records:
        df = df.iloc[sf_row_count:].copy().reset_index(drop=True)
        logger.info(f"🔍 Incremental load: skipping first {sf_row_count} records")
        logger.info(
            f"📊 Loading records {sf_row_count + 1} → {pg_total_records} "
            f"({len(df)} new records)"
        )
    elif sf_row_count >= pg_total_records:
        logger.info(
            f"👌 Snowflake already has {sf_row_count} records, PostgreSQL has {pg_total_records}. Nothing to load."
        )
        sf_conn.close()
        return
    else:
        logger.info(
            f"📋 Full load: Snowflake has {sf_row_count} records, loading all {pg_total_records} from PostgreSQL"
        )

    # Rename columns to uppercase for Snowflake
    df.columns = [c.upper() for c in df.columns]

    if df.empty:
        logger.info("👌 No new data to ingest")
        sf_conn.close()
        return

    logger.info(f"✅ Preparing {len(df)} new records for Snowflake load")

    # -------------------------------
    # Final safety check and fix
    # -------------------------------
    # Ensure timestamp columns are string type before write_pandas()
    for col in ["EVENT_TIMESTAMP", "INGESTED_AT"]:
        if col in df.columns:
            df[col] = df[col].astype(str)

    logger.info(f"🧩 Column types before load:\n{df.dtypes}")

    # -------------------------------
    # Load into Snowflake
    # -------------------------------
    try:
        success, nchunks, nrows, _ = write_pandas(
            sf_conn,
            df,
            SNOWFLAKE_POSTGRE_TABLE.split('.')[-1],
            schema=SNOWFLAKE_POSTGRE_TABLE.split('.')[0],
        )
        logger.info(
            f"✅ Successfully loaded {nrows} new records into {SNOWFLAKE_POSTGRE_TABLE}"
        )
    except Exception as e:
        logger.error(f"❌ Loading failed: {e}")
    finally:
        sf_conn.close()


# ------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------
if __name__ == "__main__":
    load_postgres_to_snowflake()