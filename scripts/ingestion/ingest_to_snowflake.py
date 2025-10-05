import os
import snowflake.connector
from dotenv import load_dotenv

STAGE_FQN = "SC_RAW_DATA.CSV_STAGE"
TABLE_FQN = "SC_RAW_DATA.raw_data"

TRACK_COLS = [
    "track_id",
    "artists",
    "album_name",
    "track_name",
    "popularity",
    "duration_ms",
    "explicit",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
    "track_genre",
]


# Get a Snowflake database connection using environment variables
def get_conn():
    load_dotenv()
    auth = os.getenv("SNOWFLAKE_AUTHENTICATOR", "SNOWFLAKE_JWT")
    kwargs = dict(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        authenticator=auth,
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        role=os.getenv("SNOWFLAKE_ROLE"),
    )
    if auth.upper() == "SNOWFLAKE_JWT":
        kwargs.update(
            private_key_file=os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PATH"),
            private_key_file_pwd=os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PWD"),
        )
    return snowflake.connector.connect(**kwargs)


# Upload a CSV file to the Snowflake stage
def upload_csv_to_stage(csv_file_path: str, overwrite=True) -> bool:
    if not csv_file_path:
        print("❌ CSV_PATH not set.")
        return False
    if not os.path.isfile(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return False
    abs_path = os.path.abspath(csv_file_path)
    put_sql = f"PUT file://{abs_path} @{STAGE_FQN}" + (
        " OVERWRITE=TRUE" if overwrite else ""
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(put_sql)
        for r in cur.fetchall():
            print(f"✅ PUT {r[0]} -> {r[1]} [{r[6]}]")
        cur.execute(f"LIST @{STAGE_FQN}")
        listed = cur.fetchall()
        print(f"📄 Files in stage: {len(listed)}")
    return True


# Load CSV data from the stage into the Snowflake table
def load_csv_to_table(pattern: str = r".*\.csv(\.gz)?") -> bool:
    columns_sql = ", ".join(TRACK_COLS)
    copy_sql = f"""
    COPY INTO {TABLE_FQN} (
        {columns_sql}
    )
    FROM @{STAGE_FQN}
    FILE_FORMAT = (
        TYPE=CSV
        FIELD_DELIMITER=','
        FIELD_OPTIONALLY_ENCLOSED_BY='"'
        SKIP_HEADER=1
        NULL_IF=('','NULL')
    )
    PATTERN = '{pattern}'
    ON_ERROR = 'ABORT_STATEMENT'
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(copy_sql)
        rows = cur.fetchall()
        if rows and len(rows[0]) == 1:
            print(f"⚠️ {rows[0][0]}")
        else:
            loaded = sum(
                1 for r in rows if len(r) > 1 and str(r[1]).upper() == "LOADED"
            )
            print(f"✅ COPY files loaded: {loaded}")
        cur.execute(f"SELECT COUNT(*) FROM {TABLE_FQN}")
        total = cur.fetchone()[0]
        print(f"📊 Row count: {total}")
    return True


# Main function to upload and load CSV data into Snowflake
def main():
    csv_path = "data\external\dataset_clean.csv"
    if upload_csv_to_stage(csv_path):
        load_csv_to_table()


if __name__ == "__main__":
    main()
