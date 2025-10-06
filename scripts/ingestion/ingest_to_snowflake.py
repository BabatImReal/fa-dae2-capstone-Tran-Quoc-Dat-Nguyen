import os
import re
import yaml
import snowflake.connector
from dotenv import load_dotenv
from pathlib import Path

# Load configuration from YAML
def load_config():
    """Load configuration from YAML file."""
    with open("config.yaml", 'r') as file:
        return yaml.safe_load(file)

config = load_config()

# Use configuration values
STAGE_FQN = config['snowflake']['stage_fqn']
TABLE_FQN = config['snowflake']['table_fqn']
TRACK_COLS = config['columns']['track']

def sanitize_identifier(identifier):
    """Sanitize SQL identifiers to prevent injection."""
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$', identifier):
        raise ValueError(f"Invalid SQL identifier: {identifier}")
    return identifier

def sanitize_file_path(file_path, base_dir=None):
    """Sanitize file paths to prevent path traversal."""
    # If base_dir is provided, ensure file_path is within it
    if base_dir:
        base_path = Path(base_dir).resolve()
        target_path = Path(file_path).resolve()
        
        # Ensure the target path is within the base directory
        if not str(target_path).startswith(str(base_path)):
            raise ValueError(f"Invalid file path: {file_path}")
        
        return str(target_path)
    
    # For absolute paths, just normalize and check for dangerous patterns
    normalized = os.path.normpath(file_path)
    if ".." in normalized:
        raise ValueError(f"Invalid file path: {file_path}")
    return normalized

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
    
    # Sanitize the file path
    try:
        abs_path = sanitize_file_path(csv_file_path)
        if not os.path.isfile(abs_path):
            print(f"❌ File not found: {abs_path}")
            return False
    except ValueError as e:
        print(f"❌ {e}")
        return False
    
    stage_fqn = sanitize_identifier(STAGE_FQN)
    
    # Construct the PUT command safely
    put_sql = f"PUT file://{abs_path} @{stage_fqn}" + (
        " OVERWRITE=TRUE" if overwrite else ""
    )
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(put_sql)
        for r in cur.fetchall():
            print(f"✅ PUT {r[0]} -> {r[1]} [{r[6]}]")
        cur.execute(f"LIST @{stage_fqn}")
        listed = cur.fetchall()
        print(f"📄 Files in stage: {len(listed)}")
    return True


# Load CSV data from the stage into the Snowflake table
def load_csv_to_table(pattern: str = r".*\.csv(\.gz)?") -> bool:
    # Sanitize inputs
    table_fqn = sanitize_identifier(TABLE_FQN)
    stage_fqn = sanitize_identifier(STAGE_FQN)
    
    columns_sql = ", ".join(TRACK_COLS)
    copy_sql = f"""
    COPY INTO {table_fqn} (
        {columns_sql}
    )
    FROM @{stage_fqn}
    FILE_FORMAT = (
        TYPE=CSV
        FIELD_DELIMITER=','
        FIELD_OPTIONALLY_ENCLOSED_BY='"'
        SKIP_HEADER=1
        NULL_IF=('','NULL')
    )
    PATTERN = %s
    ON_ERROR = 'ABORT_STATEMENT'
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(copy_sql, (pattern,))
        rows = cur.fetchall()
        if rows and len(rows[0]) == 1:
            print(f"⚠️ {rows[0][0]}")
        else:
            loaded = sum(
                1 for r in rows if len(r) > 1 and str(r[1]).upper() == "LOADED"
            )
            print(f"✅ COPY files loaded: {loaded}")
        cur.execute(f"SELECT COUNT(*) FROM {table_fqn}")
        total = cur.fetchone()[0]
        print(f"📊 Row count: {total}")
    return True


# Main function to upload and load CSV data into Snowflake
def main():
    # Use configuration for the CSV path
    csv_path = f"{config['paths']['data_dir']}/{config['paths']['cleaned_dataset']}"
    if upload_csv_to_stage(csv_path):
        load_csv_to_table()


if __name__ == "__main__":
    main()