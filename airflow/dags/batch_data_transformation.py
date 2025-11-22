"""
Batch Data Transformation DAG
Transforms raw data using dbt build command.

This DAG:
1. Runs dbt build which executes snapshots, models, and tests in order
2. Uses @task.bash for simple dbt execution with environment variables
"""

import base64
import json
import os

import pendulum
from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook


def get_dbt_snowflake_env_vars():
    """
    Get dbt Snowflake environment variables from Airflow connections.
    Decodes base64-encoded private key using Python since Jinja2 doesn't have b64decode filter.
    """

    return {
        "SNOWFLAKE_ACCOUNT": "{{ conn.snowflake_default.extra_dejson.account }}",
        "SNOWFLAKE_USER": "{{ conn.snowflake_default.login }}",
        "SNOWFLAKE_PRIVATE_KEY_FILE_PWD": "{{ conn.snowflake_default.password }}",
        "SNOWFLAKE_ROLE": "{{ conn.snowflake_default.extra_dejson.role }}",
        "SNOWFLAKE_WAREHOUSE": "{{ conn.snowflake_default.extra_dejson.warehouse }}",
        "SNOWFLAKE_DATABASE": "{{ conn.snowflake_default.extra_dejson.database }}",
        "SNOWFLAKE_SCHEMA": "{{ conn.snowflake_default.schema }}",
        "SNOWFLAKE_PRIVATE_KEY_FILE_PATH": "{{ conn.snowflake_default.extra_dejson.private_key_file }}",
        "DBT_PROFILES_DIR": "/opt/airflow/capstone_project/.dbt",
        "DBT_PROJECT_DIR": "/opt/airflow/capstone_project",
        "PATH": "/home/airflow/.local/bin:" + os.environ.get("PATH", ""),
    }


@dag(
    dag_id="batch_data_transformation",
    schedule=None,  # Only triggered by batch_data_ingestion DAG on successful completion
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["capstone", "batch-data", "dbt", "transformation"],
    max_active_runs=1,
    description="Transforms batch data using dbt build - triggered after ingestion",
)
def batch_data_transformation():
    """
    ### Batch Data Transformation DAG

    Transforms raw data using dbt build command which:
    1. **Snapshots**: Captures point-in-time data for dimension tracking
    2. **Models**: Runs staging and marts transformations
    3. **Tests**: Validates data quality

    **Dependencies**: Data must be loaded in Snowflake (from batch_data_ingestion DAG)
    **Inputs**: Raw data in SC_RAW_DATA schema
    **Outputs**: Dimension tables (snapshots) and fact/mart tables in appropriate schemas
    """

    @task.bash(env={**get_dbt_snowflake_env_vars()}, cwd="/opt/airflow/capstone_project")
    def dbt_build() -> str:
        """
        #### dbt Build Task
        Runs dbt build to execute snapshots, models, and tests in dependency order.

        dbt build:
        - Executes snapshots for slowly changing dimensions
        - Runs staging models to clean and normalize raw data
        - Builds marts layer for analytics-ready tables
        - Executes tests to validate data quality
        """
        return """
        set -e  # Exit on error
        
        echo "🏗️ Starting dbt build process..."
        echo "📂 Working directory: $(pwd)"
        echo "🔧 dbt version: $(dbt --version)"
        echo ""
        
        echo "📦 Installing dbt dependencies..."
        dbt deps
        echo ""
        
        # Run dbt build and capture exit code
        if dbt build; then
            echo ""
            echo "✅ dbt build completed successfully"
            exit 0
        else
            EXIT_CODE=$?
            echo ""
            echo "❌ dbt build failed with exit code: $EXIT_CODE"
            echo "Check the logs above for detailed error messages"
            exit $EXIT_CODE
        fi
        """

    # Execute the task
    dbt_build()


# Create the DAG instance
batch_data_transformation_dag = batch_data_transformation()