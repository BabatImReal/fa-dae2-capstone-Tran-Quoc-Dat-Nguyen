"""
dlt pipeline to load data from PostgreSQL to Snowflake.
This replaces the manual pandas-based ingestion script.
"""
import os
import logging
from typing import Iterator, Dict, Any
from pathlib import Path

import dlt
from dlt.sources.sql_database import sql_database, sql_table
from dotenv import load_dotenv
import yaml

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from YAML file."""
    project_root = Path(__file__).resolve().parents[2]
    cfg_path = project_root / "config.yaml"
    with open(cfg_path, 'r') as file:
        return yaml.safe_load(file)


def get_postgres_credentials() -> Dict[str, Any]:
    """Build PostgreSQL connection string from environment variables."""
    load_dotenv()
    
    return {
        "drivername": "postgresql",
        "database": os.getenv("POSTGRES_DB"),
        "username": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
    }


def get_snowflake_credentials() -> Dict[str, Any]:
    """Build Snowflake connection credentials from environment variables."""
    load_dotenv()
    
    # Read private key file
    private_key_path_env = os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PATH")
    private_key_pwd = os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PWD")
    
    credentials = {
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "username": os.getenv("SNOWFLAKE_USER"),
        "host": os.getenv("SNOWFLAKE_ACCOUNT"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
    }
    
    # Add private key authentication
    # dlt requires the private key content as a string, not a file path
    if private_key_path_env:
        # Try the env path first, then try project root + rsa_key.pem as fallback
        possible_paths = [
            Path(private_key_path_env),  # As specified in env
            Path(__file__).resolve().parents[2] / "rsa_key.pem",  # Project root fallback
            Path("rsa_key.pem"),  # Current directory
        ]
        
        key_path = None
        for path in possible_paths:
            try:
                if path.exists():
                    key_path = path
                    break
            except (OSError, ValueError):
                # Path might be invalid due to escape sequences
                continue
        
        if key_path and key_path.exists():
            logger.info(f"📄 Reading private key from: {key_path}")
            with open(key_path, 'rb') as f:
                private_key_bytes = f.read()
            # dlt expects the private key as a string
            credentials["private_key"] = private_key_bytes.decode('utf-8')
            if private_key_pwd:
                credentials["private_key_passphrase"] = private_key_pwd
            logger.info("✅ Private key loaded successfully")
        else:
            logger.error(f"❌ Private key file not found. Tried paths: {[str(p) for p in possible_paths]}")
            raise FileNotFoundError(f"Private key file not found at any of: {possible_paths}")
    else:
        logger.error("❌ SNOWFLAKE_PRIVATE_KEY_FILE_PATH not set in environment")
        raise ValueError("SNOWFLAKE_PRIVATE_KEY_FILE_PATH must be set for authentication")
    
    return credentials


@dlt.source
def postgres_user_events_source(
    schema: str = "staging",
    table_name: str = "user_events",
    incremental: bool = True
):
    """
    dlt source that reads user events from PostgreSQL.
    
    Args:
        schema: PostgreSQL schema name
        table_name: Table name to extract
        incremental: Whether to use incremental loading based on ingested_at
    """
    # Get PostgreSQL credentials
    postgres_creds = get_postgres_credentials()
    
    if incremental:
        # Use incremental loading based on ingested_at timestamp
        return sql_table(
            credentials=postgres_creds,
            schema=schema,
            table=table_name,
            incremental=dlt.sources.incremental(
                cursor_path="ingested_at",
                initial_value="1970-01-01T00:00:00Z",
            ),
        )
    else:
        # Full refresh
        return sql_table(
            credentials=postgres_creds,
            schema=schema,
            table=table_name,
        )


def run_postgres_to_snowflake_pipeline(
    destination_schema: str = "SC_RAW_DATA",
    destination_table: str = "RAW_DATA_POSTGRE",
    incremental: bool = True,
    write_disposition: str = "append",
) -> dlt.Pipeline:
    """
    Run the dlt pipeline to load PostgreSQL data to Snowflake.
    
    Args:
        destination_schema: Target Snowflake schema
        destination_table: Target Snowflake table name
        incremental: Enable incremental loading
        write_disposition: How to write data ('append', 'replace', 'merge')
    
    Returns:
        dlt.Pipeline: The completed pipeline
    """
    logger.info("🚀 Starting dlt pipeline: PostgreSQL → Snowflake")
    
    # Load config
    config = load_config()
    postgres_schema = config['postgresql']['schema']
    postgres_table = config['postgresql']['table']
    
    # Get Snowflake credentials
    snowflake_creds = get_snowflake_credentials()
    
    # Create dlt pipeline
    pipeline = dlt.pipeline(
        pipeline_name="postgres_to_snowflake",
        destination=dlt.destinations.snowflake(
            credentials=snowflake_creds,
        ),
        dataset_name=destination_schema,
    )
    
    # Create source
    source = postgres_user_events_source(
        schema=postgres_schema,
        table_name=postgres_table,
        incremental=incremental,
    )
    
    # Run the pipeline
    logger.info(
        f"📊 Loading from {postgres_schema}.{postgres_table} "
        f"to {destination_schema}.{destination_table}"
    )
    logger.info(f"🔄 Write disposition: {write_disposition}, Incremental: {incremental}")
    
    load_info = pipeline.run(
        source,
        table_name=destination_table,
        write_disposition=write_disposition,
    )
    
    # Log results
    logger.info(f"✅ Pipeline completed successfully!")
    logger.info(f"📈 Load info: {load_info}")
    
    # Print detailed metrics
    for package in load_info.load_packages:
        for table_name, table_metrics in package.schema_update.items():
            logger.info(f"📊 Table: {table_name}")
            logger.info(f"   Rows loaded: {table_metrics}")
    
    return pipeline


def main():
    """Main entry point for the dlt pipeline."""
    try:
        pipeline = run_postgres_to_snowflake_pipeline(
            destination_schema="SC_RAW_DATA",
            destination_table="RAW_DATA_POSTGRE",  # New table name to avoid conflicts
            incremental=True,
            write_disposition="append",
        )
        
        # Show pipeline state
        logger.info(f"📋 Pipeline state: {pipeline.state}")
        logger.info(f"🎯 Last run: {pipeline.last_trace}")
        
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
