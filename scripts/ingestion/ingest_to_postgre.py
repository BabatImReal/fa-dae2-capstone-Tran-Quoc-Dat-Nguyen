import os
import sys
import json
import yaml
from pathlib import Path
import psycopg
from dotenv import load_dotenv

# Load configuration from YAML
def load_config():
    """Load configuration from YAML file."""
    with open("config.yaml", 'r') as file:
        return yaml.safe_load(file)

config = load_config()

# Use configuration values
POSTGRES_SCHEMA = config['postgresql']['schema']
POSTGRES_TABLE = config['postgresql']['table']
MUSIC_TRANSACTION_COLS = config['columns']['music_transaction']

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
def insert_music_transactions(records):
    """
    Insert a list of music event dicts into staging.music_transactions.
    Handles the new music event structure with event_action, session_id, etc.
    Returns True if successful, False otherwise.
    """
    if not records:
        return False

    # Updated columns to match new music event data structure
    columns = MUSIC_TRANSACTION_COLS

    # Validate that columns are safe (only contain allowed characters)
    for col in columns:
        if not col.replace('_', '').isalnum():
            raise ValueError(f"Invalid column name: {col}")

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Prepare the column names and placeholders safely
                column_names = ", ".join(columns)
                placeholders = ", ".join(["%s"] * len(columns))
                
                # Prepare the query with validated components
                query = f"""
                        INSERT INTO {POSTGRES_SCHEMA}.{POSTGRES_TABLE}
                        ({column_names})
                        VALUES ({placeholders})
                        ON CONFLICT (event_id) DO NOTHING
                        """
                
                for record in records:
                    # Extract values in the correct order, handling missing fields gracefully
                    values = tuple(record.get(col) for col in columns)
                    cur.execute(query, values)
            conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting music transactions: {e}")
        return False


# Main function to load and insert music transactions into PostgreSQL
def main():
    """Main function to load and insert music transactions into PostgreSQL."""
    print("💾 PostgreSQL Data Ingestion")
    print("=" * 40)

    # Find and load the latest music transactions file
    print("\n📁 Loading music transactions data...")
    data_dir = Path(config['paths']['data_dir'])

    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return False

    # Look for the latest fake music transactions file
    json_files = sorted(data_dir.glob("fake_music_transactions_*.json"), reverse=True)
    if not json_files:
        print(f"❌ No music transaction files found in: {data_dir}")
        print("📝 Please run the fake data generator first:")
        print("   uv run scripts/ingestion/collect_fake_data.py")
        return False

    data_path = json_files[0]  # Use the latest file
    print(f"📄 Using data file: {data_path}")

    # Load and validate JSON data
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            music_transactions = json.load(f)

        if not music_transactions:
            print("❌ No data found in the file")
            return False

        print(f"📊 Loaded {len(music_transactions)} music transaction records")

    except Exception as e:
        print(f"❌ Error loading data file: {e}")
        return False

    # Insert data into PostgreSQL
    print("\n💾 Inserting data into PostgreSQL...")
    if insert_music_transactions(music_transactions):
        print(
            f"✅ Successfully inserted {len(music_transactions)} records into {POSTGRES_SCHEMA}.{POSTGRES_TABLE}"
        )
        print("\n✅ Data ingestion completed successfully!")
        return True
    else:
        print("❌ Failed to insert music transactions")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)