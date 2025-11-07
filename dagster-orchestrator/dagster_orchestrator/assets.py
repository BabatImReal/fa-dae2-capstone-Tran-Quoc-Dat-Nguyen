"""
Dagster assets for the data pipeline.
Includes batch ingestion, streaming ingestion, and dbt transformations.
"""

import sys
from pathlib import Path

# Add project root to Python path for imports
# This file is at: dagster-orchestrator/dagster_orchestrator/assets.py
# File location: .../dagster-orchestrator/dagster_orchestrator/assets.py
# Parents: [0]=dagster_orchestrator, [1]=dagster-orchestrator, [2]=project_root
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

import dlt
from dagster import (
    AssetExecutionContext,
    MaterializeResult,
    MetadataValue,
    asset,
)
from dagster_dbt import DbtCliResource, dbt_assets
from dlt.sources.sql_database import sql_table

from dagster_orchestrator.resources import (
    ConfigResource,
    PostgresResource,
    SnowflakeResource,
)


# ============================================================
# BATCH DATA INGESTION ASSETS
# ============================================================

@asset(
    group_name="batch_ingestion",
    compute_kind="python",
    description="Download Brazilian E-Commerce dataset from Kaggle",
)
def batch_csv_files(context: AssetExecutionContext, config: ConfigResource) -> MaterializeResult:
    """Download CSV files from Kaggle to local storage."""
    import sys
    from pathlib import Path
    import importlib.util
    
    # Load the module directly using absolute path
    script_path = project_root / "scripts" / "ingestion" / "collect_batch_data.py"
    spec = importlib.util.spec_from_file_location("collect_batch_data", script_path)
    collect_batch_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collect_batch_module)
    
    context.log.info("📥 Downloading batch data from Kaggle...")
    collect_batch_module.main()
    
    # Get file count
    cfg = config.get_config()
    data_dir = Path(cfg['paths']['data_dir'])
    if not data_dir.is_absolute():
        data_dir = project_root / data_dir
    csv_files = list(data_dir.glob("*.csv"))
    
    return MaterializeResult(
        metadata={
            "num_files": len(csv_files),
            "data_directory": str(data_dir),
            "file_names": MetadataValue.md("\n".join([f"- {f.name}" for f in csv_files])),
        }
    )


@asset(
    group_name="batch_ingestion",
    compute_kind="snowflake",
    deps=[batch_csv_files],
    description="Load CSV files from local storage to Snowflake raw tables",
)
def snowflake_raw_batch_data(
    context: AssetExecutionContext,
    snowflake: SnowflakeResource,
) -> MaterializeResult:
    """Upload CSV files to Snowflake staging and load into raw tables."""
    import importlib.util
    
    # Load the module directly using absolute path
    script_path = project_root / "scripts" / "ingestion" / "ingest_to_snowflake.py"
    spec = importlib.util.spec_from_file_location("ingest_to_snowflake", script_path)
    ingest_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ingest_module)
    
    context.log.info("📤 Loading batch data to Snowflake...")
    ingest_module.main()
    
    # Get row counts from Snowflake
    conn = snowflake.get_connection()
    cursor = conn.cursor()
    
    tables_loaded = []
    total_rows = 0
    
    try:
        # Query for tables in SC_RAW_DATA schema
        cursor.execute("SHOW TABLES IN SCHEMA SC_RAW_DATA")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[1]  # Table name is in second column
            cursor.execute(f"SELECT COUNT(*) FROM SC_RAW_DATA.{table_name}")
            row_count = cursor.fetchone()[0]
            tables_loaded.append(f"{table_name}: {row_count:,} rows")
            total_rows += row_count
    finally:
        cursor.close()
        conn.close()
    
    return MaterializeResult(
        metadata={
            "total_rows": total_rows,
            "tables_loaded": MetadataValue.md("\n".join([f"- {t}" for t in tables_loaded])),
        }
    )


# ============================================================
# STREAMING DATA INGESTION ASSETS (with dlt)
# ============================================================

@asset(
    group_name="streaming_ingestion",
    compute_kind="postgres",
    description="PostgreSQL table containing user events from Kafka consumer",
)
def postgres_user_events(
    context: AssetExecutionContext,
    postgres: PostgresResource,
    config: ConfigResource,
) -> MaterializeResult:
    """
    This asset represents the PostgreSQL table that gets populated by the Kafka consumer.
    We don't materialize it directly; instead we observe its state.
    """
    cfg = config.get_config()
    schema = cfg['postgresql']['schema']
    table = cfg['postgresql']['table']
    
    # Query row count
    query = f"SELECT COUNT(*) FROM {schema}.{table}"
    result = postgres.execute_query(query)
    row_count = result[0][0] if result else 0
    
    context.log.info(f"📊 PostgreSQL {schema}.{table} has {row_count:,} rows")
    
    return MaterializeResult(
        metadata={
            "row_count": row_count,
            "schema": schema,
            "table": table,
        }
    )


@asset(
    group_name="streaming_ingestion",
    compute_kind="dlt",
    deps=[postgres_user_events],
    description="Load user events from PostgreSQL to Snowflake using dlt (incremental)",
)
def snowflake_streaming_data(
    context: AssetExecutionContext,
    postgres: PostgresResource,
    snowflake: SnowflakeResource,
    config: ConfigResource,
) -> MaterializeResult:
    """
    Use dlt to incrementally load data from PostgreSQL to Snowflake.
    This replaces the manual pandas-based script.
    """
    context.log.info("🚀 Starting dlt pipeline: PostgreSQL → Snowflake")
    
    # Load configuration
    cfg = config.get_config()
    postgres_schema = cfg['postgresql']['schema']
    postgres_table = cfg['postgresql']['table']
    
    # Get credentials
    postgres_creds = postgres.get_credentials_dict()
    snowflake_creds = snowflake.get_credentials_dict()
    
    # Create dlt pipeline
    pipeline = dlt.pipeline(
        pipeline_name="postgres_to_snowflake",
        destination=dlt.destinations.snowflake(credentials=snowflake_creds),
        dataset_name="SC_RAW_DATA",
    )
    
    # Create incremental source
    source = sql_table(
        credentials=postgres_creds,
        schema=postgres_schema,
        table=postgres_table,
        incremental=dlt.sources.incremental(
            cursor_path="ingested_at",
            initial_value="1970-01-01T00:00:00Z",
        ),
    )
    
    # Run the pipeline
    context.log.info(
        f"📊 Loading from {postgres_schema}.{postgres_table} "
        f"to SC_RAW_DATA.RAW_DATA_POSTGRE"
    )
    
    load_info = pipeline.run(
        source,
        table_name="RAW_DATA_POSTGRE",
        write_disposition="append",
    )
    
    # Extract metrics
    rows_loaded = 0
    for package in load_info.load_packages:
        for table_metrics in package.schema_update.values():
            if hasattr(table_metrics, 'rows'):
                rows_loaded += table_metrics.rows
    
    context.log.info(f"✅ dlt pipeline completed! Loaded {rows_loaded:,} new rows")
    
    return MaterializeResult(
        metadata={
            "rows_loaded": rows_loaded,
            "pipeline_name": pipeline.pipeline_name,
            "destination_table": "SC_RAW_DATA.RAW_DATA_POSTGRE",
            "write_disposition": "append",
            "incremental": True,
        }
    )


# ============================================================
# DBT TRANSFORMATION ASSETS
# ============================================================

# Note: You'll need to configure this with your dbt project path
# Uncomment when dbt is ready to be orchestrated

# @dbt_assets(
#     manifest=project_root / "capstone_project" / "target" / "manifest.json",
#     project_dir=project_root / "capstone_project",
# )
# def dbt_analytics_models(context: AssetExecutionContext, dbt: DbtCliResource):
#     """All dbt models: staging, dimensions, and facts."""
#     yield from dbt.cli(["build"], context=context).stream()
