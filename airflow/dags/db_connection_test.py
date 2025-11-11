"""
Capstone DB Connection Test DAG
Tests connections to PostgreSQL and Snowflake databases.
Based on the actual capstone project patterns.
"""

import logging

import pendulum
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook


@dag(
    schedule=None,  # Manual trigger only
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    tags=["capstone", "db-connection-test", "integration"],
    max_active_runs=1,
)
def capstone_db_connection_test():
    """
    ### Capstone DB Connection Test DAG
    Tests connections to PostgreSQL and Snowflake databases.
    """

    @task()
    def test_snowflake_connection():
        """
        #### Snowflake Connection Test
        Tests connection to Snowflake and validates basic functionality.
        """
        logger = logging.getLogger(__name__)
        logger.info("🔍 Testing Snowflake connection...")

        try:
            snowflake_hook = SnowflakeHook(snowflake_conn_id="snowflake_default")
            conn = snowflake_hook.get_conn()
            cursor = conn.cursor()

            # Test basic connection
            cursor.execute("SELECT CURRENT_VERSION()")
            version = cursor.fetchone()[0]

            logger.info(f"✅ Snowflake connection successful! Version: {version}")
            cursor.close()
            conn.close()

            return f"Connected to Snowflake version {version}"
        except Exception as e:
            error_msg = f"Snowflake connection failed: {e}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)

    @task()
    def test_postgres_connection():
        """
        #### PostgreSQL Connection Test
        Tests connection to PostgreSQL and validates basic functionality.
        """
        logger = logging.getLogger(__name__)
        logger.info("🔍 Testing PostgreSQL connection...")

        try:
            pg_hook = PostgresHook(postgres_conn_id="postgres_kafka_default")
            conn = pg_hook.get_conn()
            cursor = conn.cursor()

            # Test basic connection
            cursor.execute("SELECT 1")
            test_result = cursor.fetchone()

            if test_result and test_result[0] == 1:
                logger.info("✅ PostgreSQL connection successful")
                cursor.close()
                conn.close()
                return "PostgreSQL connection verified"
            else:
                raise Exception("PostgreSQL connection test failed")
        except Exception as e:
            error_msg = f"PostgreSQL connection failed: {e}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)

    # Execute connection tests in parallel
    test_snowflake_connection()
    test_postgres_connection()

    # Both tasks run independently - no dependencies needed


# Create the DAG instance
capstone_db_connection_test()