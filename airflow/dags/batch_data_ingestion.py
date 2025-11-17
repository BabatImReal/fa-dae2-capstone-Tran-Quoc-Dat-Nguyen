"""
Batch Data Ingestion DAG
Handles data collection from Kaggle and ingestion to Snowflake.

This DAG:
1. Downloads Brazilian E-Commerce dataset from Kaggle
2. Uploads data to Snowflake raw layer
3. Triggers transformation DAG upon completion
"""

import sys
from pathlib import Path

import pendulum
from airflow.decorators import dag, task
from airflow.exceptions import AirflowException

# Add project root to path for imports (only modify path, don't import heavy modules)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
# Also add /opt/airflow to path for container imports
sys.path.insert(0, "/opt/airflow")


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
    3. **Trigger Transformation**: Starts transformation pipeline

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
        # Import heavy modules only at task execution time
        from scripts.ingestion.collect_batch_data import main as collect_batch_data

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
        # Import heavy modules only at task execution time
        from scripts.ingestion.ingest_to_snowflake import main as ingest_to_snowflake

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
    def trigger_transformation(loading_result):
        """
        #### Trigger Transformation Task
        Triggers the batch_data_transformation DAG to start immediately.
        """
        import logging
        from airflow.api.client.local_client import Client

        logging.info("🚀 Triggering batch_data_transformation DAG...")
        logging.info(f"Loading result: {loading_result}")

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
    trigger = trigger_transformation(loading)

    extraction >> loading >> trigger


# Create the DAG instance
batch_data_ingestion_dag = batch_data_ingestion()