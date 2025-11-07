"""
Dagster Definitions - Main entry point for the Dagster orchestrator.
Defines all assets, resources, jobs, and schedules.
"""

import os
from pathlib import Path

from dagster import Definitions, load_assets_from_modules
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

# Define Dagster resources
defs = Definitions(
    assets=all_assets,
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

