# If you see import errors, install psycopg2 with: pip install psycopg2-binary

import os
import sys
import json
from pathlib import Path
import psycopg
from dotenv import load_dotenv

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
    columns = [
        "event_id",
        "user_id",
        "session_id",
        "song_id",
        "song_title",
        "artist",
        "album",
        "genre",
        "duration_seconds",
        "position_seconds",
        "event_action",
        "device_type",
        "platform",
        "timestamp",
        "user_premium",
    ]

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                for record in records:
                    # Extract values in the correct order, handling missing fields gracefully
                    values = tuple(record.get(col) for col in columns)

                    cur.execute(
                        f"""
                        INSERT INTO staging.music_transactions
                        ({", ".join(columns)})
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (event_id) DO NOTHING
                        """,
                        values,
                    )
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
    data_dir = Path("data/external")

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
            f"✅ Successfully inserted {len(music_transactions)} records into staging.music_transactions"
        )
        print("\n✅ Data ingestion completed successfully!")
        return True
    else:
        print("❌ Failed to insert music transactions")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
