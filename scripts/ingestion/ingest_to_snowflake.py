# Standard library imports
import logging
import os
import re
from pathlib import Path

# Third-party imports
import snowflake.connector
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
    """Load configuration from YAML file (project root)."""
    here = Path(__file__).resolve().parents[2]
    cfg_path = here / "config.yaml"
    with open(cfg_path, 'r') as file:
        return yaml.safe_load(file)

config = load_config()

# Use configuration values
STAGE_FQN = config['snowflake']['stage_fqn']
DEFAULT_TABLE_FQN = config['snowflake'].get('table_fqn')


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
def upload_csv_to_stage(csv_file_path: str, stage_fqn: str, overwrite=True) -> bool:
    """Upload a local CSV file to the given Snowflake stage.

    Returns True on success.
    """
    if not csv_file_path:
        logger.error("CSV_PATH not set.")
        return False

    # Sanitize the file path
    try:
        abs_path = sanitize_file_path(csv_file_path)
        if not os.path.isfile(abs_path):
            logger.error(f"File not found: {abs_path}")
            return False
    except ValueError as e:
        logger.error(f"Invalid file path: {e}")
        return False

    stage = sanitize_identifier(stage_fqn)

    put_sql = f"PUT file://{abs_path} @{stage}" + (" OVERWRITE=TRUE" if overwrite else "")
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(put_sql)
        # fetch results if any
        try:
            rows = cur.fetchall()
            for r in rows:
                logger.info(f"PUT {r[0]} -> {r[1]} [{r[6]}]")
        except Exception:
            # Some connectors return no rows
            pass
        cur.execute(f"LIST @{stage}")
        listed = cur.fetchall()
        logger.info(f"📄 Files in stage {stage}: {len(listed)}")
    return True


# Mapping from config column names to Snowflake table column names
def _sanitize_col(col: str) -> str:
    """Turn column name into a safe Snowflake identifier (uppercased, underscores)."""
    return re.sub(r"[^0-9A-Za-z_]", "_", col).upper()


def create_table_if_not_exists(table_fqn: str, cols: list):
    """Create a table with VARCHAR columns (simple) plus LOADED_AT and SOURCE_SYSTEM."""
    table = sanitize_identifier(table_fqn)
    col_defs = ", ".join([f"{_sanitize_col(c)} VARCHAR" for c in cols])
    col_defs += ", LOADED_AT TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(), SOURCE_SYSTEM VARCHAR DEFAULT 'csv'"
    create_sql = f"CREATE TABLE IF NOT EXISTS {table} ({col_defs})"
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(create_sql)
        logger.info(f"✅ Ensured table exists: {table}")


def load_csv_file_from_stage_to_table(table_fqn: str, stage_fqn: str, file_pattern: str, cols: list):
    """COPY files matching pattern from stage into table using explicit column list.

    cols: list of original CSV column names (will be sanitized to SQL identifiers)
    """
    table = sanitize_identifier(table_fqn)
    stage = sanitize_identifier(stage_fqn)

    # Build target column list (sanitized) and append LOADED_AT/SOURCE_SYSTEM
    target_cols = ", ".join([_sanitize_col(c) for c in cols] + ["LOADED_AT", "SOURCE_SYSTEM"])

    # For the SELECT in COPY, we need to specify the source columns plus default values
    source_cols = ", ".join([f"${i+1}" for i in range(len(cols))])
    copy_sql = f"""
    COPY INTO {table} ({target_cols})
    FROM (
        SELECT {source_cols}, CURRENT_TIMESTAMP(), 'csv'
        FROM @{stage}
    )
    FILE_FORMAT = (
      TYPE = CSV
      FIELD_DELIMITER = ','
      FIELD_OPTIONALLY_ENCLOSED_BY = '"'
      SKIP_HEADER = 1
      NULL_IF = ('','NULL')
      ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
    )
    PATTERN = '{file_pattern}'
    ON_ERROR = 'ABORT_STATEMENT'
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(copy_sql)
        try:
            rows = cur.fetchall()
            logger.info(f"COPY result rows: {len(rows)}")
        except Exception:
            # some drivers don't return rows
            pass
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        total = cur.fetchone()[0]
        logger.info(f"📊 Row count for {table}: {total}")
    return True


# Main function to upload and load CSV data into Snowflake

def main():
    # Determine local dataset directory (prefer dlt_input_dir if present)
    project_root = Path(__file__).resolve().parents[2]
    dlt_dir = config['paths'].get('dlt_input_dir') or config['paths'].get('data_dir')
    local_data_dir = project_root / dlt_dir

    if not local_data_dir.exists():
        logger.error(f"Local data directory does not exist: {local_data_dir}")
        return

    # Derive a table namespace prefix from the stage/table config
    stage_prefix = STAGE_FQN.split('.')[0] if '.' in STAGE_FQN else STAGE_FQN

    # For each dataset configured in config['columns'], find the matching CSV and load it
    for dataset_name, cols in config.get('columns', {}).items():
        # Build expected filename patterns (files in the dataset folder)
        # e.g., key 'olist_orders' -> 'olist_orders_dataset.csv' or starting with key
        candidates = [p for p in os.listdir(local_data_dir) if p.lower().startswith(dataset_name.lower()) and p.lower().endswith('.csv')]
        if not candidates:
            logger.warning(f"No file found for dataset '{dataset_name}' in {local_data_dir}")
            continue
        # Pick the first matching file
        filename = candidates[0]
        local_path = str(local_data_dir / filename)

        # Create target table fqn under the stage prefix (e.g., SC_RAW_DATA.OLIST_ORDERS)
        target_table = f"{stage_prefix}.{dataset_name.upper()}"

        try:
            create_table_if_not_exists(target_table, cols)
        except Exception as e:
            logger.error(f"Failed to create table {target_table}: {e}")
            continue

        # Upload file to stage
        try:
            upload_csv_to_stage(local_path, STAGE_FQN, overwrite=True)
        except Exception as e:
            logger.error(f"Failed to upload {local_path} to stage {STAGE_FQN}: {e}")
            continue

        # Build a regex pattern that matches the specific uploaded file name
        escaped = re.escape(filename)
        pattern = rf".*{escaped}(\.gz)?"

        try:
            load_csv_file_from_stage_to_table(target_table, STAGE_FQN, pattern, cols)
        except Exception as e:
            logger.error(f"Failed to load {filename} into {target_table}: {e}")
            continue


if __name__ == "__main__":
    main()