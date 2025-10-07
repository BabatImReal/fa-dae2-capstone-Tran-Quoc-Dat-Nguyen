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
HOSPITAL_TRANSACTION_COLS = config['columns']['hospital_transaction']

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


# Insert a list of music event records into the staging.music_transactions table

def insert_hospital_transactions(records):
    """
    Insert a list of hospital transaction dicts into staging.hospital_transactions.
    Returns True if successful, False otherwise.
    """
    if not records:
        return False

    columns = HOSPITAL_TRANSACTION_COLS
    for col in columns:
        if not col.replace('_', '').isalnum():
            raise ValueError(f"Invalid column name: {col}")

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                column_names = ", ".join(columns)
                placeholders = ", ".join(["%s"] * len(columns))
                query = f"""
                        INSERT INTO {POSTGRES_SCHEMA}.{POSTGRES_TABLE}
                        ({column_names})
                        VALUES ({placeholders})
                        ON CONFLICT (transaction_id) DO NOTHING
                        """
                for record in records:
                    values = tuple(record.get(col) for col in columns)
                    cur.execute(query, values)
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Error inserting hospital transactions: {e}")
        return False


# Main function to load and insert music transactions into PostgreSQL

def main():
    """Main function to load and insert hospital transactions into PostgreSQL."""
    logger.info("💾 PostgreSQL Data Ingestion")
    logger.info("=" * 40)

    # Find and load the latest hospital transactions file
    logger.info("📁 Loading hospital transactions data...")
    data_dir = Path(config['paths']['data_dir'])

    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return False

    # Look for the latest fake hospital transactions file
    json_files = sorted(data_dir.glob("fake_hospital_transactions_*.json"), reverse=True)
    if not json_files:
        logger.error(f"No hospital transaction files found in: {data_dir}")
        logger.info("📝 Please run the fake data generator first:")
        logger.info("   uv run scripts/ingestion/collect_fake_data.py")
        return False

    data_path = json_files[0]  # Use the latest file
    logger.info(f"📄 Using data file: {data_path}")

    # Load and validate JSON data
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            hospital_transactions = json.load(f)

        if not hospital_transactions:
            logger.error("No data found in the file")
            return False

        logger.info(f"📊 Loaded {len(hospital_transactions)} hospital transaction records")

    except Exception as e:
        logger.error(f"Error loading data file: {e}")
        return False

    # Insert data into PostgreSQL
    logger.info("💾 Inserting data into PostgreSQL...")
    if insert_hospital_transactions(hospital_transactions):
        logger.info(
            f"✅ Successfully inserted {len(hospital_transactions)} records into "
            f"{POSTGRES_SCHEMA}.{POSTGRES_TABLE}"
        )
        logger.info("✅ Data ingestion completed successfully!")
        return True
    else:
        logger.error("❌ Failed to insert hospital transactions")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)