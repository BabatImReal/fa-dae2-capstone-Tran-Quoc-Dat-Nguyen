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
from dagster_dbt import DbtCliResource, dbt_assets, DagsterDbtTranslator
from dlt.sources.sql_database import sql_table

from dagster_orchestrator.resources import (
    ConfigResource,
    PostgresResource,
    SnowflakeResource,
)


# ============================================================
# DBT TRANSLATOR - Customize dbt asset properties
# ============================================================

class CustomDbtTranslator(DagsterDbtTranslator):
    """Custom translator to set group name for all dbt assets."""
    
    def get_group_name(self, dbt_resource_props):
        """Assign all dbt assets to the dbt_transformation group."""
        return "dbt_transformation"


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
# DBT TRANSFORMATION ASSETS
# ============================================================

@dbt_assets(
    manifest=project_root / "capstone_project" / "target" / "manifest.json",
    dagster_dbt_translator=CustomDbtTranslator(),
)
def dbt_analytics_models(context: AssetExecutionContext, dbt: DbtCliResource):
    """
    All dbt models: staging, intermediate, and marts.
    
    Dependencies:
    - Staging models depend on raw Snowflake tables
    - Intermediate models process staged data
    - Mart models create final dimensional/fact tables
    """
    yield from dbt.cli(["build"], context=context).stream()
