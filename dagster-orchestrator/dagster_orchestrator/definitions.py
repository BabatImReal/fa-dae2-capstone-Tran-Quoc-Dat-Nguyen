"""
Dagster Definitions - Main entry point for the Dagster orchestrator.
Defines all assets, resources, jobs, and schedules.
"""

from dagster import Definitions, load_assets_from_modules
from dagster_dbt import DbtCliResource

from dagster_orchestrator import assets
from dagster_orchestrator.resources import (
    ConfigResource,
    PostgresResource,
    SnowflakeResource,
)

# Load all assets
all_assets = load_assets_from_modules([assets])

# Define Dagster resources
defs = Definitions(
    assets=all_assets,
    resources={
        # Configuration
        "config": ConfigResource(),
        
        # Database connections
        "postgres": PostgresResource.from_env(),
        "snowflake": SnowflakeResource.from_env(),
        
        # dbt (uncomment when ready)
        # "dbt": DbtCliResource(project_dir="../capstone_project"),
    },
)

