# Standard library imports
import json
import logging
import os
import sys
from pathlib import Path

# Third-party imports
import psycopg
import yaml
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Load configuration from YAML
def load_config():
    """Load configuration from YAML file."""
    with open("config.yaml", 'r') as file:
        return yaml.safe_load(file)

config = load_config()

# Use configuration values
POSTGRES_SCHEMA = config['postgresql']['schema']
POSTGRES_TABLE = config['postgresql']['table']
USER_EVENT_COLS = config['columns']['user_events']

# Load environment variables
load_dotenv()


# Get a PostgreSQL database connection using environment variables
def get_connection():
    """Get database connection using environment variables."""
    params = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "dbname": os.getenv("POSTGRES_DB", "staging_db"),
        "user": os.getenv("POSTGRES_USER", "staging_user"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }
    return psycopg.connect(**params)


def create_table_if_not_exists():
    """
    Create the schema and user_events table if they don't exist.
    Returns True if successful, False otherwise.
    """
    try:
        # Get database connection string for autocommit mode
        params = {
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": os.getenv("POSTGRES_PORT", "5432"),
            "dbname": os.getenv("POSTGRES_DB", "staging_db"),
            "user": os.getenv("POSTGRES_USER", "staging_user"),
            "password": os.getenv("POSTGRES_PASSWORD"),
        }
        dsn = " ".join([f"{k}={v}" for k, v in params.items() if v])
        
        with (
            psycopg.connect(dsn, autocommit=True) as conn,
            conn.cursor() as cur,
        ):
            # Create schema if not exists - using sql.Identifier for safety
            from psycopg import sql
            cur.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(POSTGRES_SCHEMA)
                )
            )
            
            # Create table with all necessary columns
            cur.execute(
                sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {}.{} (
                        event_id VARCHAR(255) PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        session_id VARCHAR(255) NOT NULL,
                        event_type VARCHAR(100) NOT NULL,
                        event_timestamp TIMESTAMP NOT NULL,
                        user_agent TEXT,
                        ip_address VARCHAR(45),
                        page_url TEXT,
                        page_title TEXT,
                        referrer TEXT,
                        product_id VARCHAR(255),
                        product_name TEXT,
                        category VARCHAR(100),
                        price NUMERIC(10, 2),
                        quantity INTEGER,
                        search_query TEXT,
                        results_count INTEGER,
                        filters_applied BOOLEAN,
                        checkout_step VARCHAR(100),
                        cart_value NUMERIC(10, 2),
                        item_count INTEGER,
                        ingested_at TIMESTAMP NOT NULL
                    )
                """).format(
                    sql.Identifier(POSTGRES_SCHEMA),
                    sql.Identifier(POSTGRES_TABLE)
                )
            )
            
            # Create indexes for better query performance
            cur.execute(
                sql.SQL("""
                    CREATE INDEX IF NOT EXISTS idx_user_id 
                    ON {}.{}(user_id)
                """).format(
                    sql.Identifier(POSTGRES_SCHEMA),
                    sql.Identifier(POSTGRES_TABLE)
                )
            )
            cur.execute(
                sql.SQL("""
                    CREATE INDEX IF NOT EXISTS idx_event_timestamp 
                    ON {}.{}(event_timestamp)
                """).format(
                    sql.Identifier(POSTGRES_SCHEMA),
                    sql.Identifier(POSTGRES_TABLE)
                )
            )
            cur.execute(
                sql.SQL("""
                    CREATE INDEX IF NOT EXISTS idx_event_type 
                    ON {}.{}(event_type)
                """).format(
                    sql.Identifier(POSTGRES_SCHEMA),
                    sql.Identifier(POSTGRES_TABLE)
                )
            )
        logger.info(f"✅ Table {POSTGRES_SCHEMA}.{POSTGRES_TABLE} is ready")
        return True
    except Exception as e:
        logger.error(f"Error creating table: {e}")
        return False


def insert_single_user_event(record):
    """
    Insert a single user event dict into staging.user_events.
    Returns True if successful, False otherwise.
    """
    if not record:
        return False

    columns = USER_EVENT_COLS
    for col in columns:
        if not col.replace('_', '').isalnum():
            raise ValueError(f"Invalid column name: {col}")

    try:
        from psycopg import sql
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Use sql.SQL and sql.Identifier to prevent SQL injection
                query = sql.SQL("""
                    INSERT INTO {}.{} ({})
                    VALUES ({})
                    ON CONFLICT (event_id) DO NOTHING
                """).format(
                    sql.Identifier(POSTGRES_SCHEMA),
                    sql.Identifier(POSTGRES_TABLE),
                    sql.SQL(", ").join(map(sql.Identifier, columns)),
                    sql.SQL(", ").join(sql.Placeholder() * len(columns))
                )
                
                values = tuple(record.get(col) for col in columns)
                cur.execute(query, values)
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error inserting user event: {e}")
        return False

