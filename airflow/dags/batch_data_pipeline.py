"""
Batch Data Pipeline DAGs
Separates ingestion and transformation into two independent DAGs.

DAG 1: batch_data_ingestion_dag
- Collects batch data from Kaggle
- Ingests it to Snowflake

DAG 2: batch_data_transformation_dag
- Runs dbt snapshots
- Runs dbt staging models
- Runs dbt marts models
- Runs dbt tests
- Generates report
"""

import os
import sys
from pathlib import Path

import pendulum
from airflow.decorators import dag, task
from airflow.exceptions import AirflowException

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Import scripts
from scripts.ingestion.collect_batch_data import main as collect_batch_data
from scripts.ingestion.ingest_to_snowflake import main as ingest_to_snowflake


# ============================================================================
# DAG 1: BATCH DATA INGESTION
# ============================================================================


@dag(
    dag_id="batch_data_ingestion",
    schedule="0 2 * * 0",  # Weekly at 2 AM on Sundays
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["capstone", "batch-data", "ingestion"],
    max_active_runs=1,
    description="Collects batch data from Kaggle and ingests to Snowflake",
)
def batch_data_ingestion():
    """
    ### Batch Data Ingestion DAG

    Handles the complete data ingestion workflow:
    1. **Data Collection**: Downloads Kaggle datasets
    2. **Data Loading**: Uploads data to Snowflake

    **Dependencies**: Snowflake connection and Kaggle credentials configured
    **Outputs**: Data loaded in Snowflake RAW layer (SC_RAW_DATA schema)
    """

    @task()
    def extract_batch_data():
        """
        #### Extract Task
        Downloads batch data from Kaggle.

        Uses credentials from ~/.kaggle/kaggle.json
        Extracts to configured dlt_input_dir path
        """
        import logging

        logging.info("🔄 Starting batch data collection from Kaggle...")

        try:
            collect_batch_data()
            logging.info("✅ Batch data collection completed successfully")
            return {
                "status": "success",
                "message": "Data collected from Kaggle",
                "timestamp": pendulum.now().isoformat(),
            }
        except Exception as e:
            logging.error(f"❌ Failed to collect batch data: {str(e)}")
            raise AirflowException(f"Data collection failed: {str(e)}")

    @task()
    def load_to_snowflake(extraction_result):
        """
        #### Load Task
        Uploads data from local storage to Snowflake stage and creates/populates tables.

        Steps:
        - Uploads CSV files to Snowflake stage
        - Creates tables if they don't exist
        - Copies data from stage to tables

        **Output Tables**: Created in SC_RAW_DATA schema
        """
        import logging

        logging.info("📤 Starting data ingestion to Snowflake...")
        logging.info(f"Extraction result: {extraction_result}")

        try:
            ingest_to_snowflake()
            logging.info("✅ Data ingestion to Snowflake completed successfully")
            return {
                "status": "success",
                "message": "Data loaded to Snowflake",
                "timestamp": pendulum.now().isoformat(),
            }
        except Exception as e:
            logging.error(f"❌ Failed to ingest data to Snowflake: {str(e)}")
            raise AirflowException(f"Data ingestion failed: {str(e)}")

    @task()
    def ingestion_complete(loading_result):
        """
        #### Ingestion Complete Task
        Marks ingestion as complete and logs summary.
        """
        import json
        import logging

        logging.info("✅ Batch data ingestion pipeline complete")
        logging.info(f"Final result: {json.dumps(loading_result, indent=2)}")

        return {
            "ingestion_status": "complete",
            "timestamp": pendulum.now().isoformat(),
        }

    @task()
    def trigger_transformation(completion_result):
        """
        #### Trigger Transformation Task
        Triggers the batch_data_transformation DAG to start immediately.
        """
        import logging
        from airflow.api.client.local_client import Client

        logging.info("🚀 Triggering batch_data_transformation DAG...")
        logging.info(f"Ingestion completion result: {completion_result}")

        try:
            client = Client(None, None)
            run = client.trigger_dag(
                dag_id="batch_data_transformation",
                execution_date=pendulum.now(),
                replace_microseconds=False,
            )
            logging.info(f"✅ Successfully triggered transformation DAG: {run}")
            return {
                "trigger_status": "success",
                "triggered_dag_run_id": str(run),
                "timestamp": pendulum.now().isoformat(),
            }
        except Exception as e:
            logging.error(f"⚠️ Failed to trigger transformation DAG: {str(e)}")
            # Don't fail the ingestion DAG if trigger fails
            return {
                "trigger_status": "failed",
                "error": str(e),
                "timestamp": pendulum.now().isoformat(),
            }

    # Task dependencies for ingestion DAG
    extraction = extract_batch_data()
    loading = load_to_snowflake(extraction)
    completion = ingestion_complete(loading)
    trigger = trigger_transformation(completion)

    extraction >> loading >> completion >> trigger


# ============================================================================
# DAG 2: BATCH DATA TRANSFORMATION
# ============================================================================


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

        Models transform raw data from Snowflake stage into clean, normalized tables.
        """
        import logging
        import subprocess

        logging.info("🏗️ Running dbt staging models...")
        logging.info(f"Previous task result: {snapshot_result}")

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

        Models create business-ready aggregated tables from staging layer.
        """
        import logging
        import subprocess

        logging.info("🏪 Running dbt marts models...")
        logging.info(f"Previous task result: {staging_result}")

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

        Executes both generic and custom tests defined in dbt project.
        """
        import logging
        import subprocess

        logging.info("🧪 Running dbt tests...")
        logging.info(f"Previous task result: {marts_result}")

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


# ============================================================================
# CREATE DAG INSTANCES
# ============================================================================

batch_data_ingestion_dag = batch_data_ingestion()
batch_data_transformation_dag = batch_data_transformation()
