import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import psycopg
from langchain.tools import tool

load_dotenv()

# Get a PostgreSQL database connection using environment variables
def get_connection():
    """Get database connection using environment variables."""
    params = {
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "connect_timeout": 10,  # 10 second timeout
    }
    # Debug: print connection params (mask password)
    print(f"🔌 PostgreSQL Connection Params:")
    print(f"   Host: {params['host']}")
    print(f"   Port: {params['port']}")
    print(f"   Database: {params['dbname']}")
    print(f"   User: {params['user']}")
    print(f"   Password: {'*' * len(params['password']) if params['password'] else 'None'}")
    return psycopg.connect(**params)

@tool
def get_latest_product_summary_from_postgre() -> Dict[str, Any]:
    """
    Return the latest ingested product event from PostgreSQL.
    Query the most recent product event from staging.user_events.
    Returns: product_name, category, price, quantity.
    """

    sql = """
        SELECT
            product_name,
            category,
            price,
            quantity
        FROM staging.user_events
        ORDER BY ingested_at DESC
        LIMIT 1
    """.strip()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)

    row = cur.fetchone()
    columns = [desc[0] for desc in cur.description]

    cur.close()
    conn.close()

    return {
        "sql_used": sql,
        "row_count": 1 if row else 0,
        "row": dict(zip(columns, row)) if row else None
    }