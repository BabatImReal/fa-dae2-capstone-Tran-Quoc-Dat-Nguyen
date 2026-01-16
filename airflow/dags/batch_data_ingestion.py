"""
Batch Data Ingestion DAG
Handles data collection from Kaggle and ingestion to Snowflake.

This DAG:
1. Downloads Brazilian E-Commerce dataset from Kaggle
2. Uploads data to Snowflake raw layer
"""

import sys
from pathlib import Path

import pendulum
from airflow.decorators import dag, task

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, "/opt/airflow")


@dag(
    dag_id="batch_data_ingestion",
    schedule=None,
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    catchup=False,
    tags=["capstone", "ingestion", "snowflake"],
    max_active_runs=1,
    description="Downloads data from Kaggle and loads to Snowflake",
)
def batch_data_ingestion():
    """
    Batch Data Ingestion Workflow:
    1. Extract: Download Brazilian E-Commerce dataset from Kaggle
    2. Load: Upload CSVs to Snowflake stage and load into tables
    """

    @task()
    def extract_from_kaggle():
        """Download batch data from Kaggle to /opt/airflow/data/external/"""
        from scripts.ingestion.collect_batch_data import main as collect_data
        
        print("🔽 Downloading data from Kaggle...")
        collect_data()
        print("✅ Data downloaded successfully")
        return {"status": "success", "timestamp": pendulum.now().isoformat()}

    @task()
    def load_to_snowflake(extract_result):
        """Upload CSVs to Snowflake and load into SC_RAW_DATA schema"""
        from scripts.ingestion.ingest_to_snowflake import main as ingest_data
        
        print(f"📤 Loading data to Snowflake... (Extract: {extract_result['status']})")
        ingest_data()
        print("✅ Data loaded to Snowflake successfully")
        return {"status": "success", "timestamp": pendulum.now().isoformat()}

    # Define task dependencies
    extract_result = extract_from_kaggle()
    load_result = load_to_snowflake(extract_result)
    
    extract_result >> load_result


# Instantiate the DAG
batch_data_ingestion_dag = batch_data_ingestion()