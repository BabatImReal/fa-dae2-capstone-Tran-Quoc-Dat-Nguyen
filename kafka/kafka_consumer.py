from datetime import datetime
import json
import os
from pathlib import Path
import sys

from confluent_kafka import Consumer
from dotenv import load_dotenv
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from config.models import UserEventMessage
from scripts.ingestion.ingest_to_postgre import (
    create_table_if_not_exists,
    insert_single_user_event,
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from YAML file."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as file:
        return yaml.safe_load(file)


def main() -> None:
    load_dotenv()

    # Initialize PostgreSQL table
    if not create_table_if_not_exists():
        logger.error("Failed to create user_events table. Exiting.")
        return

    # Kafka configuration from environment
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "user_events")
    group_id = os.getenv("KAFKA_CONSUMER_GROUP", "user-events-consumer")

    # Configure Kafka consumer with production-ready settings
    consumer_config = {
        "bootstrap.servers": bootstrap,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    }

    logger.info(f"Connecting to Kafka at: {bootstrap}")
    logger.info(
        f"Consumer config: group_id={consumer_config['group.id']}, "
        f"auto_commit={consumer_config['enable.auto.commit']}"
    )

    consumer = Consumer(consumer_config)
    consumer.subscribe([topic])
    logger.info(f"Subscribed to topic: {topic}")

    rows_written = 0
    messages_processed = 0

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            if msg.error():
                logger.error(f"Kafka error: {msg.error()}")
                continue

            try:
                event_dict = json.loads(msg.value().decode("utf-8"))
                messages_processed += 1

                # Parse event with Pydantic model for validation
                event = UserEventMessage(**event_dict)

                # Add ingested_at timestamp
                ingested_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

                # Convert to UserEventData for database insertion
                user_event_data = event.to_user_event_data(ingested_at=ingested_at)

                # Insert into PostgreSQL
                if insert_single_user_event(user_event_data.to_dict()):
                    rows_written += 1
                    logger.info(
                        f"✅ Inserted event_id={user_event_data.event_id} | "
                        f"user_id={user_event_data.user_id} | "
                        f"event_type={user_event_data.event_type} "
                        f"(row #{rows_written})"
                    )

                if messages_processed % 10 == 0:
                    logger.info(
                        f"Progress: {messages_processed} messages processed, "
                        f"{rows_written} rows written"
                    )

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)

    except KeyboardInterrupt:
        logger.info(
            f"Shutdown. Final stats: {messages_processed} messages, "
            f"{rows_written} rows written"
        )
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
