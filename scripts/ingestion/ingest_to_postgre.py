# If you see import errors, install psycopg2 with: pip install psycopg2-binary

import os
import psycopg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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
        "event_id", "user_id", "session_id", "song_id", "song_title", "artist",
        "album", "genre", "duration_seconds", "position_seconds", "event_action",
        "device_type", "platform", "timestamp", "user_premium"
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
                        ({', '.join(columns)})
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (event_id) DO NOTHING
                        """,
                        values
                    )
            conn.commit()
        return True
    except Exception as e:
        print(f"Error inserting music transactions: {e}")
        return False
