# 🏗️ Capstone Project Architecture

## Overview

This architecture supports an end-to-end music data pipeline with both batch and real-time processing. Batch ingestion moves data to Snowflake, where dbt is used for transformations. Real-time source streams data to Kafka, which then loads into PostgreSQL. Both Snowflake and PostgreSQL provide data to the AI agent layer. All components are containerized with Docker; Dagster orchestrates batch, dbt, and PostgreSQL workflows, while Kafka operates outside Dagster.

## System Diagram

![Architecture Diagram](diagram\architecture.png)
