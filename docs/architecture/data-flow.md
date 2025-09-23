# 🔄 Data Flow Documentation

## 📋 Overview

This document explains the data flow for the Music Pipeline using a visual diagram. The pipeline supports both batch and real-time data sources, orchestrated by Dagster and containerized with Docker. Batch data (Kaggle dataset) is loaded into Snowflake and transformed with dbt. Real-time (fake) data is streamed via Kafka into PostgreSQL. Both Snowflake and PostgreSQL provide data to the AI Agent and RAG system.

## 📊 Data Flow Diagram


**Diagram Explanation:**
- **Batch Data Source (Kaggle Dataset):** Ingested into the Data Warehouse (Snowflake).
- **Transformation (dbt):** Runs inside Snowflake for data cleaning and modeling.
- **Stream Data Source (Fake Data):** Sent to Data Streaming (Apache Kafka).
- **Kafka:** Streams data into the Local Database (PostgreSQL).
- **Dagster:** Orchestrates batch, transformation, and database workflows (all inside Docker).
- **Snowflake & PostgreSQL:** Serve as sources for the AI Agent.
- **AI Agent:** Consumes data from both databases and interacts with the RAG system for document processing.

**Step-by-Step Data Flow:**

### 1. Batch Data Ingestion
- **Source:** Kaggle Spotify Tracks Dataset (CSV)
- **Process:** Python scripts extract and validate batch data.
- **Orchestration:** Dagster schedules and manages ingestion jobs.
- **Destination:** Data is loaded into Snowflake (RAW tables).

### 2. Batch Data Transformation
- **Tool:** dbt (data build tool) runs inside Snowflake.
- **Process:** dbt cleans, models, and enriches batch data for analytics.
- **Output:** Transformed data is stored in Snowflake ANALYTICS tables.

### 3. Real-Time Data Ingestion
- **Source:** Faker-generated synthetic music events.
- **Process:** Python scripts generate and send events to Kafka.
- **Streaming:** Kafka acts as the message broker for real-time data.
- **Orchestration:** Dagster manages downstream ingestion from Kafka.
- **Destination:** Events are loaded into PostgreSQL staging tables.

### 4. Real-Time Data Transformation
- **Tool:** dbt (optionally) for cleaning and modeling in PostgreSQL.
- **Process:** Data is validated, deduplicated, and structured for downstream use.

### 5. AI Agent Consumption
- **Sources:** Both Snowflake (batch analytics) and PostgreSQL (real-time events).
- **Process:** AI agent queries both databases for recommendations, metadata, and analytics.
- **Output:** Results are provided to users or downstream applications.

### 6. RAG System & Document Processing
- **Process:** AI agent leverages RAG (Retrieval-Augmented Generation) for advanced queries and document (PDF) processing.

### 7. Monitoring & Quality Checks
- **Tools:** Dagster, dbt tests, SQL queries.
- **Process:** Monitor pipeline health, validate data quality, and handle errors.

> All major components (Dagster, Kafka, databases) are containerized using Docker for portability and reproducibility.

## 📝 Summary

This architecture enables robust, scalable, and flexible data movement from ingestion to analytics and AI, supporting both batch and real-time use cases.