"""
Type definitions for the User Events streaming pipeline.

This module contains Pydantic model definitions for structured data used across
the application, providing better type safety, validation, and IDE support.
"""

from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class PostgresConfig(BaseModel):
    """PostgreSQL connection configuration."""

    model_config = ConfigDict(frozen=True)

    user: str
    password: str
    host: str
    port: str
    database: str
    schema: str
    table: str


class KafkaConfig(BaseModel):
    """Kafka connection configuration."""

    model_config = ConfigDict(frozen=True)

    bootstrap_servers: str
    topic: str


class UserEventData(BaseModel):
    """
    User event data structure for database operations.

    Fields match the staging.user_events table schema.
    """

    model_config = ConfigDict(strict=True)

    event_id: str
    user_id: str
    session_id: str
    event_type: str
    event_timestamp: str
    user_agent: str
    ip_address: str
    page_url: str
    page_title: str
    referrer: str
    product_id: str
    product_name: str
    category: str
    price: float
    quantity: int
    search_query: str
    results_count: int
    filters_applied: bool
    checkout_step: str
    cart_value: float
    item_count: int
    ingested_at: str

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return self.model_dump()


class UserEventMessage(BaseModel):
    """
    User event message structure for Kafka streaming.

    This is the payload that will be sent through Kafka topics.
    """

    model_config = ConfigDict(strict=True)

    event_id: str
    user_id: str
    session_id: str
    event_type: str
    event_timestamp: str
    user_agent: str
    ip_address: str
    page_url: str
    page_title: str
    referrer: str
    product_id: str
    product_name: str
    category: str
    price: float
    quantity: int
    search_query: str
    results_count: int
    filters_applied: bool
    checkout_step: str
    cart_value: float
    item_count: int

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return self.model_dump()

    def to_user_event_data(self, ingested_at: str) -> UserEventData:
        """Convert message to user event data for database operations."""
        return UserEventData(
            event_id=self.event_id,
            user_id=self.user_id,
            session_id=self.session_id,
            event_type=self.event_type,
            event_timestamp=self.event_timestamp,
            user_agent=self.user_agent,
            ip_address=self.ip_address,
            page_url=self.page_url,
            page_title=self.page_title,
            referrer=self.referrer,
            product_id=self.product_id,
            product_name=self.product_name,
            category=self.category,
            price=self.price,
            quantity=self.quantity,
            search_query=self.search_query,
            results_count=self.results_count,
            filters_applied=self.filters_applied,
            checkout_step=self.checkout_step,
            cart_value=self.cart_value,
            item_count=self.item_count,
            ingested_at=ingested_at,
        )
