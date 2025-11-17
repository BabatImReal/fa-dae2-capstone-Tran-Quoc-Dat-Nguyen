"""
Batch Data Transformation DAG
Transforms raw data using dbt build command.

This DAG:
1. Runs dbt build which executes snapshots, models, and tests in order
2. Generates execution report
"""

import os
from pathlib import Path

import pendulum
from airflow.decorators import dag, task
from airflow.exceptions import AirflowException

# Project root for dbt commands
PROJECT_ROOT = Path(__file__).resolve().parents[2]


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

    @task()
    def run_dbt_build():
        """
        #### dbt Build Task
        Runs dbt build to execute snapshots, models, and tests in dependency order.

        dbt build:
        - Executes snapshots for slowly changing dimensions
        - Runs staging models to clean and normalize raw data
        - Builds marts layer for analytics-ready tables
        - Executes tests to validate data quality
        """
        import logging
        import subprocess

        logging.info("🏗️ Running dbt build...")

        try:
            # Change to dbt project directory
            dbt_project_path = PROJECT_ROOT / "capstone_project"
            os.chdir(dbt_project_path)

            # Run dbt build (includes snapshots, run, test)
            result = subprocess.run(
                ["dbt", "build"],
                check=True,
                capture_output=True,
                text=True,
            )

            logging.info("dbt build output:")
            logging.info(result.stdout)
            logging.info("✅ dbt build executed successfully")

            return {
                "status": "success",
                "message": "dbt build completed",
                "timestamp": pendulum.now().isoformat(),
            }
        except subprocess.CalledProcessError as e:
            logging.error(f"❌ dbt build failed: {e.stderr}")
            raise AirflowException(f"dbt build execution failed: {e.stderr}")
        except Exception as e:
            logging.error(f"❌ Unexpected error in dbt build: {str(e)}")
            raise AirflowException(f"dbt build failed: {str(e)}")

    # Execute the task
    run_dbt_build()


# Create the DAG instance
batch_data_transformation_dag = batch_data_transformation()