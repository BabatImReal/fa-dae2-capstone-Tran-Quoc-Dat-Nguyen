#!/usr/bin/env python3
"""
Test script to verify Kafka and PostgreSQL setup
"""

from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import os

from confluent_kafka import Consumer, Producer
from dotenv import load_dotenv
import yaml

from config.logger import logger

try:
    import psycopg
except ImportError:
    logger.error("❌ psycopg not installed. Run: uv add psycopg")
    sys.exit(1)


def load_config():
    """Load configuration from YAML file."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as file:
        return yaml.safe_load(file)


def test_kafka_connection():
    """Test Kafka connection and basic operations"""
    try:
        bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        logger.info(f"Testing Kafka connection to {bootstrap}")

        # Test producer connection
        producer = Producer({"bootstrap.servers": bootstrap})
        producer.flush(5)
        logger.info("✅ Kafka producer connection successful")

        # Test consumer connection
        consumer = Consumer(
            {
                "bootstrap.servers": bootstrap,
                "group.id": "test_group",
                "auto.offset.reset": "earliest",
            }
        )
        consumer.close()
        logger.info("✅ Kafka consumer connection successful")

        return True

    except Exception as e:
        logger.error(f"❌ Kafka test failed: {e}")
        return False


def test_postgres_connection():
    """Test PostgreSQL connection and basic operations"""
    try:
        # Load PostgreSQL config from environment
        user = os.getenv("POSTGRES_USER")
        password = os.getenv("POSTGRES_PASSWORD")
        host = os.getenv("POSTGRES_HOST")
        port = os.getenv("POSTGRES_PORT")
        database = os.getenv("POSTGRES_DB")

        # Check if required variables are set
        if not password:
            logger.error("❌ POSTGRES_PASSWORD environment variable is not set")
            logger.info("💡 Please check your .env file")
            return False

        if not user:
            logger.error("❌ POSTGRES_USER environment variable is not set")
            return False

        # Build proper DSN with all components
        dsn = (
            f"host={host} port={port} dbname={database} user={user} password={password}"
        )
        logger.info(f"Testing PostgreSQL connection to {user}@{host}:{port}/{database}")

        with (
            psycopg.connect(dsn, autocommit=True) as conn,
            conn.cursor() as cur,
        ):
            # Test basic query
            cur.execute("SELECT version()")
            version = cur.fetchone()
            logger.info(f"✅ PostgreSQL connection successful: {version[0][:50]}...")

            # Test schema and table creation
            config = load_config()
            schema = config["postgresql"]["schema"]

            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema}.test_setup (
                    id SERIAL PRIMARY KEY,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Test insert
            cur.execute(
                f"INSERT INTO {schema}.test_setup (message) VALUES (%s)",
                ("Setup test successful",),
            )

            # Test select
            cur.execute(f"SELECT COUNT(*) FROM {schema}.test_setup")
            count = cur.fetchone()
            logger.info(f"✅ PostgreSQL operations successful: {count[0]} test records")

        return True

    except psycopg.OperationalError as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        logger.info("💡 Troubleshooting tips:")
        logger.info("   1. Check if PostgreSQL is running: docker ps")
        logger.info("   2. Verify .env file has correct credentials")
        logger.info("   3. Check docker-compose.yml port mappings")
        logger.info("   4. Try: docker-compose restart postgres")
        return False
    except Exception as e:
        logger.error(f"❌ PostgreSQL test failed: {e}")
        return False


def main():
    """Run all tests"""
    load_dotenv()

    logger.info("🚀 Starting setup verification...")

    # Show environment variables being used
    logger.info("\n📋 Configuration:")
    logger.info(
        f"   KAFKA_BOOTSTRAP_SERVERS: {os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')}"
    )
    logger.info(f"   POSTGRES_HOST: {os.getenv('POSTGRES_HOST', 'localhost')}")
    logger.info(f"   POSTGRES_PORT: {os.getenv('POSTGRES_PORT', '5432')}")
    logger.info(f"   POSTGRES_DB: {os.getenv('POSTGRES_DB', 'staging_db')}")
    logger.info(f"   POSTGRES_USER: {os.getenv('POSTGRES_USER', 'staging_user')}")
    logger.info("")

    kafka_ok = test_kafka_connection()
    postgres_ok = test_postgres_connection()

    logger.info("\n" + "=" * 50)
    logger.info("📊 SETUP VERIFICATION RESULTS")
    logger.info("=" * 50)

    if kafka_ok:
        logger.info("✅ Kafka: Ready")
    else:
        logger.error("❌ Kafka: Failed")

    if postgres_ok:
        logger.info("✅ PostgreSQL: Ready")
    else:
        logger.error("❌ PostgreSQL: Failed")

    if kafka_ok and postgres_ok:
        logger.info("\n🎉 All systems ready! You can now run the lab.")
        logger.info("📖 Next steps:")
        logger.info("   1. Start consumer: python kafka/kafka_consumer.py")
        logger.info("   2. Start producer: python kafka/kafka_producer.py")
        logger.info("   3. Monitor with Kafdrop: http://localhost:9000")
    else:
        logger.error("\n⚠️  Some systems failed. Please check the setup.")
        sys.exit(1)


if __name__ == "__main__":
    main()
