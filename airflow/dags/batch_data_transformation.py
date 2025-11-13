"""
Batch Data Transformation DAG
Transforms raw data using dbt (snapshots, staging, marts, tests).

This DAG:
1. Captures point-in-time snapshots for dimension tracking
2. Transforms raw data to staging layer
3. Creates business-ready mart tables
4. Validates data quality with tests
5. Generates execution reports
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
    description="Transforms batch data using dbt (snapshots, staging, marts, tests) - triggered after ingestion",
)
def batch_data_transformation():
    """
    ### Batch Data Transformation DAG

    Transforms raw data using dbt:
    1. **Snapshots**: Captures point-in-time data for dimension tracking
    2. **Staging**: Cleans and normalizes raw data
    3. **Marts**: Creates business-ready aggregated tables
    4. **Tests**: Validates data quality
    5. **Report**: Generates execution summary

    **Dependencies**: Data must be loaded in Snowflake (from batch_data_ingestion DAG)
    **Inputs**: Raw data in SC_RAW_DATA schema
    **Outputs**: Dimension tables (snapshots) and fact/mart tables in appropriate schemas
    """

    @task()
    def run_dbt_snapshots():
        """
        #### dbt Snapshots Task
        Runs dbt snapshots to capture point-in-time data changes.

        Snapshots create dimension tables that track slowly changing dimensions.
        Includes:
        - customer_snapshot
        - order_snapshot
        - product_snapshot
        - seller_snapshot
        - order_payment_snapshot
        - order_review_snapshot
        """
        import logging
        import subprocess

        logging.info("📸 Running dbt snapshots...")

        try:
            # Change to dbt project directory
            dbt_project_path = PROJECT_ROOT / "capstone_project"
            os.chdir(dbt_project_path)

            # Run dbt snapshots
            result = subprocess.run(
                ["dbt", "snapshot"],
                check=True,
                capture_output=True,
                text=True,
            )

            logging.info("dbt snapshot output:", result.stdout)
            logging.info("✅ dbt snapshots executed successfully")

            return {
                "status": "success",
                "message": "dbt snapshots completed",
                "timestamp": pendulum.now().isoformat(),
            }
        except subprocess.CalledProcessError as e:
            logging.error(f"❌ dbt snapshots failed: {e.stderr}")
            raise AirflowException(f"dbt snapshots execution failed: {e.stderr}")
        except Exception as e:
            logging.error(f"❌ Unexpected error in dbt snapshots: {str(e)}")
            raise AirflowException(f"dbt snapshots failed: {str(e)}")

    @task()
    def run_dbt_staging(snapshot_result):
        """
        #### dbt Staging Task
        Runs dbt models in staging layer.

        Transforms raw data from Snowflake stage into clean, normalized tables.
        Applies business logic, data cleaning, and standardization.

        **Output Schema**: STAGING
        """
        import logging
        import subprocess

        logging.info("🏗️ Running dbt staging models...")
        logging.info(f"Snapshots result: {snapshot_result}")

        try:
            # Change to dbt project directory
            dbt_project_path = PROJECT_ROOT / "capstone_project"
            os.chdir(dbt_project_path)

            # Run dbt staging models
            result = subprocess.run(
                ["dbt", "run", "--select", "path:models/staging"],
                check=True,
                capture_output=True,
                text=True,
            )

            logging.info("dbt stdout:", result.stdout)
            logging.info("✅ dbt staging models executed successfully")

            return {
                "status": "success",
                "message": "dbt staging models completed",
                "timestamp": pendulum.now().isoformat(),
            }
        except subprocess.CalledProcessError as e:
            logging.error(f"❌ dbt staging models failed: {e.stderr}")
            raise AirflowException(f"dbt staging execution failed: {e.stderr}")
        except Exception as e:
            logging.error(f"❌ Unexpected error in dbt staging: {str(e)}")
            raise AirflowException(f"dbt staging failed: {str(e)}")

    @task()
    def run_dbt_marts(staging_result):
        """
        #### dbt Marts Task
        Runs dbt models in marts layer.

        Creates business-ready aggregated and fact tables from staging layer.
        Optimized for reporting and analytics.

        **Output Schema**: MARTS
        """
        import logging
        import subprocess

        logging.info("🏪 Running dbt marts models...")
        logging.info(f"Staging result: {staging_result}")

        try:
            # Change to dbt project directory
            dbt_project_path = PROJECT_ROOT / "capstone_project"
            os.chdir(dbt_project_path)

            # Run dbt marts models
            result = subprocess.run(
                ["dbt", "run", "--select", "path:models/marts"],
                check=True,
                capture_output=True,
                text=True,
            )

            logging.info("dbt stdout:", result.stdout)
            logging.info("✅ dbt marts models executed successfully")

            return {
                "status": "success",
                "message": "dbt marts models completed",
                "timestamp": pendulum.now().isoformat(),
            }
        except subprocess.CalledProcessError as e:
            logging.error(f"❌ dbt marts models failed: {e.stderr}")
            raise AirflowException(f"dbt marts execution failed: {e.stderr}")
        except Exception as e:
            logging.error(f"❌ Unexpected error in dbt marts: {str(e)}")
            raise AirflowException(f"dbt marts failed: {str(e)}")

    @task()
    def run_dbt_tests(marts_result):
        """
        #### dbt Tests Task
        Runs dbt tests to validate data quality.

        Executes both generic tests (unique, not_null, relationships)
        and custom tests defined in dbt project.

        **Tests**: Check data integrity, relationships, and business rules
        """
        import logging
        import subprocess

        logging.info("🧪 Running dbt tests...")
        logging.info(f"Marts result: {marts_result}")

        try:
            # Change to dbt project directory
            dbt_project_path = PROJECT_ROOT / "capstone_project"
            os.chdir(dbt_project_path)

            # Run dbt tests
            result = subprocess.run(
                ["dbt", "test"],
                check=True,
                capture_output=True,
                text=True,
            )

            logging.info("dbt test output:", result.stdout)
            logging.info("✅ dbt tests executed successfully")

            return {
                "status": "success",
                "message": "dbt tests completed",
                "timestamp": pendulum.now().isoformat(),
            }
        except subprocess.CalledProcessError as e:
            logging.warning(f"⚠️ Some dbt tests failed: {e.stderr}")
            # Don't raise exception for test failures, just warn
            return {
                "status": "warning",
                "message": "Some dbt tests failed",
                "error_details": e.stderr,
                "timestamp": pendulum.now().isoformat(),
            }
        except Exception as e:
            logging.error(f"❌ Unexpected error in dbt tests: {str(e)}")
            raise AirflowException(f"dbt tests failed: {str(e)}")

    @task()
    def generate_transformation_report(test_result):
        """
        #### Report Generation Task
        Generates a comprehensive transformation execution report.

        Summarizes all dbt stages: snapshots, staging, marts, and tests.
        """
        import json
        import logging

        logging.info("📋 Generating transformation report...")

        report = {
            "pipeline_summary": {
                "dag_id": "batch_data_transformation",
                "execution_timestamp": pendulum.now().isoformat(),
                "status": test_result.get("status", "success"),
            },
            "transformation_stages": {
                "snapshots": "Point-in-time snapshots created for dimension tracking",
                "staging": "Raw data transformed to staging layer",
                "marts": "Business-ready models created",
                "testing": "Data quality tests executed",
            },
            "metadata": {
                "project_root": str(PROJECT_ROOT),
                "dbt_project": str(PROJECT_ROOT / "capstone_project"),
                "version": "1.0",
            },
        }

        logging.info("Transformation Report:")
        logging.info(json.dumps(report, indent=2))

        return report

    # Task dependencies for transformation DAG
    snapshots = run_dbt_snapshots()
    staging = run_dbt_staging(snapshots)
    marts = run_dbt_marts(staging)
    tests = run_dbt_tests(marts)
    report = generate_transformation_report(tests)

    snapshots >> staging >> marts >> tests >> report


# Create the DAG instance
batch_data_transformation_dag = batch_data_transformation()