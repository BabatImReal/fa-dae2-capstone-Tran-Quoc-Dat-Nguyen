import os
import json
import sys

import psycopg
from dotenv import load_dotenv
from langgraph.checkpoint.postgres import PostgresSaver

load_dotenv()


def get_connection():
    """Create PostgreSQL connection"""
    host = os.getenv("LANGGRAPH_POSTGRES_HOST")
    port = os.getenv("LANGGRAPH_POSTGRES_PORT")
    database = os.getenv("LANGGRAPH_POSTGRES_DB")
    user = os.getenv("LANGGRAPH_POSTGRES_USER")
    password = os.getenv("LANGGRAPH_POSTGRES_PASSWORD")
    
    return psycopg.connect(
        f"postgresql://{user}:{password}@{host}:{port}/{database}",
        autocommit=True
    )


def get_thread_ids(connection):
    """Get all thread IDs from database"""
    with connection.cursor() as cur:
        cur.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id")
        return [row[0] for row in cur.fetchall()]


def main():
    connection = get_connection()
    checkpointer = PostgresSaver(connection)
    
    if len(sys.argv) > 1:
        # Query specific thread
        thread_id = sys.argv[1]
        config = {"configurable": {"thread_id": thread_id}}
        state = checkpointer.get(config)
        if state:
            print(json.dumps(state, indent=2, default=str))
    else:
        # Query all threads
        thread_ids = get_thread_ids(connection)
        for thread_id in thread_ids:
            config = {"configurable": {"thread_id": thread_id}}
            state = checkpointer.get(config)
            if state:
                print(f"=== {thread_id} ===")
                print(json.dumps(state, indent=2, default=str))
                print()
    
    connection.close()


if __name__ == "__main__":
    main()
    