# 🛠️ Architecture Decision Records (ADRs)

## 📋 Overview

This document contains Architecture Decision Records for our **Music Pipeline** capstone project.

> **📚 Foundation**: Our technology choices support the fundamental data flow: Sources → Ingestion → Storage → Transformation → Analysis.

---

## Decision: PostgreSQL for Local Development

**Status**: Approved

**Context**:  
We need a local database for development and staging of music data before sending to cloud. The database must handle JSON data from music APIs (Last.fm, Spotify) and support rapid development iterations. This addresses the "Where do we store it?" question for local development.

**Decision**:  
Use PostgreSQL in Docker containers for local development and staging.

**Rationale** (OLTP Pattern for Staging):  
- **ACID Compliance**: Ensures data integrity for music metadata (transactional)
- **JSON Support**: Native JSON/JSONB types for API responses
- **SQL Ecosystem**: Seamless integration with dbt and Python
- **Docker Ready**: Consistent environment across team
- **Production Similarity**: Skills transfer to cloud PostgreSQL services
- **Fast Transactions**: Perfect for staging and validation workflows

**Alternatives Considered**:  
- **SQLite**: Too limited for complex JSON operations and concurrent access
- **MySQL**: Weaker JSON support compared to PostgreSQL
- **MongoDB**: NoSQL complexity not needed for structured music data

**Consequences**:  
- ✅ Fast local development and testing
- ✅ Easy transition to cloud PostgreSQL
- ✅ OLTP optimized for staging workflows
- ⚠️ Requires Docker knowledge
- ⚠️ Additional local resource usage

**Example**:  
Store raw Last.fm API responses in JSONB columns, then query with `->` operators for flexible data exploration during development.

---

## Decision: Snowflake for Cloud Data Warehouse

**Status**: Approved

**Context**:  
We need a cloud data warehouse that can handle large-scale music data, support ML workloads, and provide cost-effective scaling for our AI recommendation engine. This addresses the "Where do we store it?" question for production analytics.

**Decision**:  
Use Snowflake as our cloud data warehouse with separate RAW and ANALYTICS databases.

**Rationale** (OLAP Pattern for Analytics):  
- **Separation of Storage & Compute**: Pay only when processing data (cost-effective)
- **VARIANT Data Type**: Perfect for diverse music API responses
- **Auto-scaling**: Handles varying workloads (daily batch vs. real-time queries)
- **ML-Ready**: Built-in functions for recommendation algorithms
- **Time Travel**: Essential for data governance and debugging
- **OLAP Optimized**: Designed for analytical queries and aggregations

**Alternatives Considered**:  
- **BigQuery**: Google ecosystem lock-in concerns
- **Redshift**: More complex maintenance and scaling
- **Databricks**: Overkill for our use case, higher complexity

**Consequences**:  
- ✅ Excellent performance for music analytics
- ✅ Cost-effective with auto-scaling
- ✅ Native JSON handling for APIs
- ✅ OLAP optimized for BI and ML workloads
- ⚠️ Vendor-specific SQL extensions
- ⚠️ Learning curve for Snowflake-specific features

**Example**:  
Load raw JSON from music APIs into RAW.MUSIC.TRACKS, then use dbt to transform into dimensional models in ANALYTICS.MUSIC schema.

---

## Decision: Python 3.10+ for Data Processing

**Status**: Approved

**Context**:  
We need a programming language for data collection, processing, and ML model development that can handle music APIs and integrate well with our data stack. This addresses the "How does it move?" and "How do we process it?" questions.

**Decision**:  
Use Python 3.10+ as our primary language for all data processing tasks.

**Rationale** (Ingestion & Transformation):  
- **Music API Ecosystem**: Rich libraries (spotipy, pylast, requests) for ingestion
- **Data Processing**: Mature tools (pandas, polars) for music metadata transformation
- **ML/AI Libraries**: Best-in-class ecosystem (scikit-learn, tensorflow) for recommendations
- **Async Support**: Concurrent API calls for better performance
- **Integration**: Native support for dbt, Airflow, Snowflake
- **ETL/ELT Support**: Perfect for both extract and transform phases

**Alternatives Considered**:  
- **Java**: Verbose for data processing, less ML ecosystem
- **R**: Strong for analytics but limited deployment options
- **Scala**: Learning curve too steep for team

**Consequences**:  
- ✅ Fastest development for music data pipelines
- ✅ Excellent ML/AI ecosystem
- ✅ Strong community and documentation
- ✅ Perfect for both ingestion and transformation
- ⚠️ Performance limitations for very large datasets
- ⚠️ GIL limitations for CPU-intensive tasks

**Example**:  
Build async API collectors for Last.fm and Spotify, use pandas for data cleaning, and scikit-learn for recommendation algorithms.

---

## Decision: dbt for Data Transformation

**Status**: Approved

**Context**:  
We need a tool to transform raw music data into analytics-ready models with proper testing, documentation, and version control. This directly addresses the "How do we process it?" question in our ELT approach.

**Decision**:  
Use dbt (data build tool) for all data transformations in Snowflake.

**Rationale** (ELT Transformation Layer):  
- **SQL-First**: Leverages team's SQL knowledge for transformations
- **Testing Framework**: Built-in data quality tests
- **Documentation**: Auto-generated data lineage
- **Version Control**: Git-based workflow for transformation logic
- **Snowflake Integration**: Native support and optimization
- **ELT Pattern**: Perfect for transform-in-warehouse approach

**Alternatives Considered**:  
- **Python ETL**: More complex, harder to maintain, doesn't leverage warehouse
- **Stored Procedures**: Vendor-specific, limited version control
- **Airflow Tasks**: Mixing orchestration with transformation

**Consequences**:  
- ✅ Clean separation of transformation logic
- ✅ Excellent testing and documentation
- ✅ Version-controlled transformations
- ✅ Optimized for ELT pattern
- ⚠️ Another tool to learn and maintain
- ⚠️ SQL-only limitations for complex logic

**Example**:  
Create staging models to clean raw music data, then build dimensional models (dim_artists, dim_tracks) for analytics and ML features.

---

## Decision: Dagster for Orchestration 

**Status**: Approved

**Context**:  
We need a modern orchestration tool to manage scheduling, monitoring, and error handling across batch and real-time pipelines (Kaggle, Faker, Kafka, PostgreSQL, Snowflake, dbt). Dagster must coordinate containerized workflows and support modular pipeline design.

**Decision**:  
Use Dagster for orchestration and scheduling of all pipeline components.

**Rationale** (Pipeline Orchestration):  
- **Python Native**: Seamless integration with Python-based ingestion and transformation
- **Rich Operators**: Built-in support for Snowflake, dbt, PostgreSQL, Kafka
- **Containerization**: Works well with Docker for local and cloud deployments
- **Monitoring**: Web UI for pipeline visibility and health checks
- **Error Handling**: Retry logic, alerting, and failure recovery
- **Modular Design**: Supports reusable, composable pipeline assets
- **Workflow Management**: Ideal for complex ELT and streaming coordination

**Alternatives Considered**:  
- **Prefect**: Less mature, smaller ecosystem
- **Apache Airflow**: More complex setup, less modular for Python-first teams
- **Cron Jobs**: No monitoring, dependency management, or error handling

**Consequences**:  
- ✅ Unified orchestration for batch, streaming, and transformation
- ✅ Excellent monitoring and alerting
- ✅ Strong Python and Docker integration
- ✅ Modular, maintainable pipeline design
- ⚠️ Requires learning Dagster concepts
- ⚠️ Additional infrastructure for Dagster UI and scheduler

**Example**:  
Dagster schedules and orchestrates batch ingestion from Kaggle to Snowflake, triggers dbt transformations, manages real-time ingestion from Faker to Kafka and PostgreSQL, and coordinates downstream AI agent workflows.

---

## Decision: Kafka for Real-Time Streaming
  
**Status**: Approved

**Context**:  
We need a robust solution for real-time data streaming between microservices and data pipelines, especially for user activity events and real-time recommendations. This addresses the "How does it move?" question for real-time data.

**Decision**:  
Use Kafka for all real-time data streaming needs.

**Rationale** (Event Streaming):  
- **High Throughput**: Handles large volumes of events (user actions, API calls)
- **Low Latency**: Real-time processing for immediate insights
- **Durability**: Persistent storage of event logs
- **Scalability**: Easily scales with increased event load
- **Stream Processing**: Integrates with tools like Faust for real-time analytics
- **Decoupling**: Microservices can evolve independently

**Alternatives Considered**:  
- **RabbitMQ**: More complex routing, less suitable for high-throughput
- **AWS Kinesis**: Vendor lock-in, less control over infrastructure
- **Redis Streams**: Limited stream processing capabilities

**Consequences**:  
- ✅ Immediate processing of user events
- ✅ Scalable architecture for data pipelines
- ✅ Durable event storage
- ⚠️ Added complexity in managing Kafka cluster
- ⚠️ Learning curve for Kafka ecosystem

**Example**:  
Stream user activity events from FastAPI to Kafka, process in real-time with Faust, and update PostgreSQL and Snowflake for analytics and recommendations.

---

## Decision: uv for Package Management

**Status**: Approved  
**Why**: Fast, modern Python package/dependency management.  
**How**: Used for reproducible environment setup and dependency resolution.

---

## Decision: pytest & great-expectations for Testing

**Status**: Approved  
**Why**: pytest for unit/integration tests; great-expectations for data quality validation.  
**How**: Used in CI/CD and local development to ensure code and data reliability.

---

## Decision: Git + GitHub for Version Control

**Status**: Approved  
**Why**: Industry-standard distributed version control and collaboration.  
**How**: All code, dbt models, and documentation managed in GitHub repositories.

---

## Decision: Docker for Containerization

**Status**: Approved  
**Why**: Consistent, portable environments for all pipeline components.  
**How**: All major services (Dagster, Kafka, PostgreSQL, dbt, Python scripts) run in Docker containers.

---

## Summary Table

| Technology           | Purpose                | Status    | Key Benefit           | Containerized | Orchestrated By |
|----------------------|------------------------|-----------|-----------------------|---------------|-----------------|
| PostgreSQL           | Local OLTP staging     | ✅        | Fast dev, ACID        | Docker        | Dagster         |
| Snowflake            | Cloud OLAP analytics   | ✅        | Scalable, ML-ready    | -             | Dagster         |
| Python 3.10+         | Ingestion, ML, ETL     | ✅        | Rich ecosystem        | Docker        | Dagster         |
| dbt                  | SQL transformation     | ✅        | Testable, versioned   | Docker        | Dagster         |
| Dagster              | Orchestration          | ✅        | Modern, Python-native | Docker        | -               |
| Kafka                | Real-time streaming    | ✅        | Scalable events       | Docker        | -               |
| uv                   | Package management     | ✅        | Fast, reproducible    | -             | -               |
| pytest               | Unit/integration tests | ✅        | Reliable code testing | -             | -               |
| great-expectations   | Data validation        | ✅        | Data quality checks   | -             | -               |
| Git + GitHub         | Version control        | ✅        | Collaboration         | -             | -               |
| Docker               | Containerization       | ✅        | Portability           | -             | -               |

---


## Conclusion

Our technology stack is purpose-built for the **Music Pipeline**:

1. **PostgreSQL** provides reliable, flexible local development with production similarity
2. **Snowflake** offers cloud-scale analytics with built-in music data optimization
3. **Python** delivers the richest ecosystem for music APIs and ML development

This combination ensures we can **build locally, scale globally** while leveraging industry-standard tools that provide maximum learning value and career transferability.