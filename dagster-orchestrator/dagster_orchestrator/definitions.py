"""
Dagster Definitions - Main entry point for the Dagster orchestrator.
Defines all assets, resources, jobs, and schedules.
"""

import os
from pathlib import Path

from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_modules,
)
from dagster_dbt import DbtCliResource

from dagster_orchestrator import assets
from dagster_orchestrator.resources import (
    ConfigResource,
    PostgresResource,
    SnowflakeResource,
)

# Get project root (3 levels up: definitions.py -> dagster_orchestrator -> dagster-orchestrator -> project_root)
project_root = Path(__file__).resolve().parents[2]
dbt_project_dir = project_root / "capstone_project"

# Load all assets
all_assets = load_assets_from_modules([assets])

# ============================================================
# DEFINE JOBS
# ============================================================

# Batch ingestion job: Download from Kaggle → Upload to Snowflake
batch_ingestion_job = define_asset_job(
    name="batch_ingestion_job",
    selection=AssetSelection.groups("batch_ingestion"),
    description="Download batch data from Kaggle and load to Snowflake",
)

# Streaming ingestion job: Observe PostgreSQL → Load to Snowflake with dlt
streaming_ingestion_job = define_asset_job(
    name="streaming_ingestion_job",
    selection=AssetSelection.groups("streaming_ingestion"),
    description="Incrementally load streaming data from PostgreSQL to Snowflake",
)

# dbt transformation job: Run all dbt models (staging, marts, etc.)
# Note: dbt_assets creates multiple assets, so we select by tag or all dbt models
dbt_transformation_job = define_asset_job(
    name="dbt_transformation_job",
    selection=AssetSelection.groups("dbt_transformation"),
    description="Run all dbt models: staging, intermediate, and marts",
)

# Full pipeline job: Run everything in sequence
full_pipeline_job = define_asset_job(
    name="full_pipeline_job",
    selection=AssetSelection.all(),
    description="Run the complete data pipeline from ingestion to transformation",
)

# ============================================================
# DEFINE SCHEDULES
# ============================================================

# Schedule for batch ingestion (daily at 1 AM)
batch_ingestion_schedule = ScheduleDefinition(
    name="batch_ingestion_schedule",
    job=batch_ingestion_job,
    cron_schedule="0 1 * * *",  # Daily at 1 AM
    description="Download batch data from Kaggle daily at 1 AM",
)

# Schedule for streaming data ingestion (every 15 minutes)
streaming_ingestion_schedule = ScheduleDefinition(
    name="streaming_ingestion_schedule",
    job=streaming_ingestion_job,
    cron_schedule="*/15 * * * *",  # Every 15 minutes
    description="Incrementally load streaming data every 15 minutes",
)

# Schedule for dbt transformation (daily at 2 AM, after batch ingestion)
dbt_transformation_schedule = ScheduleDefinition(
    name="dbt_transformation_schedule",
    job=dbt_transformation_job,
    cron_schedule="0 2 * * *",  # Daily at 2 AM
    description="Run dbt transformations daily at 2 AM",
)

# Schedule for full pipeline (weekly on Sunday at midnight)
full_pipeline_schedule = ScheduleDefinition(
    name="full_pipeline_schedule",
    job=full_pipeline_job,
    cron_schedule="0 0 * * 0",  # Weekly on Sunday at midnight
    description="Run complete pipeline weekly on Sunday",
)

# Define Dagster resources
defs = Definitions(
    assets=all_assets,
    jobs=[
        batch_ingestion_job,
        streaming_ingestion_job,
        dbt_transformation_job,
        full_pipeline_job,
    ],
    schedules=[
        batch_ingestion_schedule,
        streaming_ingestion_schedule,
        dbt_transformation_schedule,
        full_pipeline_schedule,
    ],
    resources={
        # Configuration
        "config": ConfigResource(),
        
        # Database connections
        "postgres": PostgresResource.from_env(),
        "snowflake": SnowflakeResource.from_env(),
        
        # dbt
        "dbt": DbtCliResource(
            project_dir=os.fspath(dbt_project_dir),
            profiles_dir=os.fspath(dbt_project_dir),
        ),
    },
)

