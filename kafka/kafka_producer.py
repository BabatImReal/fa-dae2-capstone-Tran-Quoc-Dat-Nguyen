import json
import os
from pathlib import Path
import sys
import time

from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
from dotenv import load_dotenv
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from config.models import UserEventMessage
from scripts.ingestion.collect_fake_data import FakeDataGenerator

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


def delivery_callback(err, msg):
    """Callback for Kafka message delivery confirmation"""
    if err:
        logger.error(f"Delivery failed: {err}")
    else:
        logger.debug(
            f"Message delivered to {msg.topic()}[{msg.partition()}] "
            f"@ offset {msg.offset()}"
        )


def create_kafka_topic(bootstrap_servers: str, topic_name: str) -> bool:
    """Create Kafka topic if it doesn't exist"""
    try:
        admin_client = AdminClient({"bootstrap.servers": bootstrap_servers})

        # Check if topic already exists
        metadata = admin_client.list_topics(timeout=10)
        if topic_name in metadata.topics:
            logger.info(f"Topic '{topic_name}' already exists")
            return True

        # Create new topic
        new_topic = NewTopic(topic=topic_name, num_partitions=1, replication_factor=1)

        fs = admin_client.create_topics([new_topic])

        # Wait for topic creation to complete
        for topic, f in fs.items():
            try:
                f.result()  # The result itself is None
                logger.info(f"✅ Topic '{topic}' created successfully")
                return True
            except Exception as e:
                logger.error(f"❌ Failed to create topic '{topic}': {e}")
                return False

    except Exception as e:
        logger.error(f"❌ Error creating topic: {e}")
        return False


def main() -> None:
    load_dotenv()

    # Initialize fake data generator
    generator = FakeDataGenerator()

    # Kafka configuration from environment
    bootstrap = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "user_events")

    logger.info(f"Connecting to Kafka at: {bootstrap}")

    # Create topic if it doesn't exist
    logger.info("Creating Kafka topic...")
    if not create_kafka_topic(bootstrap, topic):
        logger.error("Failed to create topic. Exiting.")
        return

    # Configure producer
    producer = Producer(
        {
            "bootstrap.servers": bootstrap,
            "client.id": "user-events-producer",
            "acks": "all",
        }
    )

    try:
        message_count = 0
        logger.info("Starting to produce user event messages...")

        while True:
            # Generate single user event
            event_data = generator.generate_single_user_event()

            # Validate with Pydantic model
            event = UserEventMessage(**event_data)

            # Produce to Kafka
            producer.produce(
                topic,
                key=event.event_id,
                value=json.dumps(event.to_dict()),
                callback=delivery_callback,
            )
            producer.poll(0)  # Trigger delivery reports

            message_count += 1
            logger.info(
                f"📊 Produced message #{message_count}: event_id={event.event_id} | "
                f"user_id={event.user_id} | event_type={event.event_type} | "
                f"timestamp={event.event_timestamp}"
            )

            if message_count % 10 == 0:
                logger.info(f"Total messages produced: {message_count}")

            time.sleep(10.0)  # Produce 1 event every 10 seconds

    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        producer.flush(10.0)
        logger.info(f"Producer shutdown complete. Total messages: {message_count}")


if __name__ == "__main__":
    main()
