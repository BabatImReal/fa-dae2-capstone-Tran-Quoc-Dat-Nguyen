"""
Centralized configuration management for the Kafka streaming lab.

This module provides consistent access to environment variables and default
configuration values across all components of the application.
"""

import os

from config.models import KafkaConfig, PostgresConfig


def get_postgres_config() -> PostgresConfig:
    """
    Get PostgreSQL configuration from environment variables.

    Returns:
        PostgresConfig object containing PostgreSQL connection parameters with
        consistent defaults.
    """
    return PostgresConfig(
        user=os.getenv("POSTGRES_USER", "staging_user"),
        password=os.getenv("POSTGRES_PASSWORD", "Quocdat@123"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "staging_db"),
    )


def get_kafka_config() -> KafkaConfig:
    """
    Get Kafka configuration from environment variables.

    Returns:
        KafkaConfig object containing Kafka connection parameters with
        consistent defaults.
    """
    return KafkaConfig(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
        topic=os.getenv("KAFKA_TOPIC"),
    )
