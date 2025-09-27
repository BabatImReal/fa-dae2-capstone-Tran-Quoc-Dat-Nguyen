import os
import snowflake.connector
from dotenv import load_dotenv

STAGE_FQN = "SC_RAW_DATA.CSV_STAGE"
TABLE_FQN = "SC_RAW_DATA.test_raw_data"
CSV_DEFAULT = "sample_data.csv"

def get_conn():
    load_dotenv()
    return snowflake.connector.connect(
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

def ensure_table():
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_FQN} (
        id INTEGER,
        data_content STRING,
        file_name STRING,
        loaded_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
    );
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(ddl)

def upload_csv_to_stage(csv_file_path: str, overwrite=True):
    if not os.path.isfile(csv_file_path):
        print(f"❌ File not found: {csv_file_path}")
        return False
    abs_path = os.path.abspath(csv_file_path)
    put_sql = f"PUT file://{abs_path} @{STAGE_FQN}"
    if overwrite:
        put_sql += " OVERWRITE=TRUE"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(put_sql)
        rows = cur.fetchall()
        for r in rows:
            print(f"✅ PUT {r[0]} -> {r[1]} [{r[6]}]")
        cur.execute(f"LIST @{STAGE_FQN}")
        listed = cur.fetchall()
        print(f"📄 Stage file count: {len(listed)}")
    return True

def load_csv_to_table(pattern=None):
    # Allow .csv or .csv.gz if pattern not supplied
    pat = pattern or r".*\.csv(\.gz)?"
    copy_sql = f"""
    COPY INTO {TABLE_FQN} (id, data_content, file_name)
    FROM @{STAGE_FQN}
    FILE_FORMAT=(TYPE=CSV FIELD_OPTIONALLY_ENCLOSED_BY='"' SKIP_HEADER=1 NULL_IF=('','NULL'))
    PATTERN='{pat}'
    ON_ERROR='CONTINUE';
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(copy_sql)
        rows = cur.fetchall()
        if rows and len(rows[0]) == 1:
            # Summary only (no files matched)
            print(f"⚠️  {rows[0][0]}")
            loaded_files = 0
        else:
            loaded_files = sum(1 for r in rows if len(r) > 1 and str(r[1]).upper() == "LOADED")
        print(f"✅ COPY files loaded: {loaded_files}")
        cur.execute(f"SELECT COUNT(*) FROM {TABLE_FQN}")
        count = cur.fetchone()[0]
        print(f"📊 Table row count: {count}")

def main():
    csv_path = os.getenv("CSV_PATH", CSV_DEFAULT)
    ensure_table()
    if upload_csv_to_stage(csv_path):
        load_csv_to_table()

if __name__ == "__main__":
    main()