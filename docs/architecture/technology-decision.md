# 🛠️ Architecture Decision Records (ADRs)

## 📋 Overview

This document contains Architecture Decision Records for our **AI Music Recommender Agent** capstone project. Each decision follows our ADR template and aligns with [data engineering fundamentals](data-engineering-fundamentals.md) - answering the five core questions of where data comes from, how it moves, where it's stored, how it's processed, and how it's used.

> **📚 Foundation**: Our technology choices support the fundamental data flow: Sources → Ingestion → Storage → Transformation → Analysis.

---

## Decision: PostgreSQL for Local Development

**Date**: 2024-01-15  
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

**Date**: 2024-01-15  
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

**Date**: 2024-01-15  
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

**Date**: 2024-01-15  
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

## Decision: Apache Airflow for Orchestration

**Date**: 2024-01-15  
**Status**: Proposed

**Context**:  
We need to orchestrate our music data pipeline with scheduling, monitoring, and error handling across multiple systems (APIs, PostgreSQL, Snowflake, dbt). This addresses the "How does it move?" question for pipeline coordination.

**Decision**:  
Use Apache Airflow for pipeline orchestration and scheduling.

**Rationale** (Pipeline Orchestration):  
- **Python Native**: Fits with our Python-first approach
- **Rich Operators**: Built-in support for our tech stack (Snowflake, dbt, PostgreSQL)
- **Monitoring**: Web UI for pipeline visibility
- **Error Handling**: Retry logic and alerting
- **Industry Standard**: Widely adopted in data engineering
- **Workflow Management**: Perfect for complex ELT pipeline coordination

**Alternatives Considered**:  
- **Prefect**: Newer but less mature ecosystem
- **Dagster**: Complex for our use case
- **Cron Jobs**: Too simple, no monitoring or dependencies

**Consequences**:  
- ✅ Professional pipeline orchestration
- ✅ Excellent monitoring and alerting
- ✅ Strong community and ecosystem
- ✅ Perfect for coordinating ELT workflows
- ⚠️ Resource intensive (requires dedicated infrastructure)
- ⚠️ Complex setup and maintenance

**Example**:  
Daily DAG that collects music data from APIs, loads to Snowflake, runs dbt transformations, and triggers ML model retraining.

---

## Summary

| Technology | Purpose | Status | Key Benefit | Data Engineering Function |
|------------|---------|--------|-------------|---------------------------|
| PostgreSQL | Local Development | ✅ Approved | Fast iteration | Staging (OLTP) |
| Snowflake | Cloud Warehouse | ✅ Approved | Scalable analytics | Storage & Analytics (OLAP) |
| Python 3.10+ | Data Processing | ✅ Approved | Rich ecosystem | Ingestion & Transformation |
| dbt | Data Transformation | ✅ Approved | SQL-first approach | Transform (ELT) |
| Airflow | Orchestration | 🔄 Proposed | Professional pipeline | Orchestration |

This technology stack provides a modern, scalable foundation for our **AI Music Recommender Agent** while emphasizing learning industry-standard tools and following proven data engineering patterns.

## 🔄 Supporting the Five Fundamental Questions

### 1. Where does data come from? (Sources)
- **Music APIs**: Last.fm, Spotify for real-time data
- **Kaggle Datasets**: Historical music data for training

### 2. How does it move? (Ingestion & Transport)
- **Python**: API collectors and batch processors
- **Airflow**: Pipeline orchestration and scheduling

### 3. Where do we store it? (Storage)
- **PostgreSQL**: Local staging (OLTP)
- **Snowflake**: Cloud analytics (OLAP)

### 4. How do we process it? (Transformation)
- **dbt**: SQL-first transformations in warehouse
- **Python**: Complex processing and ML feature engineering

### 5. How do we use it? (Analysis & Output)
- **Snowflake ANALYTICS**: Dimensional models for BI
- **Python ML**: AI recommendation engine
- **REST APIs**: Real-time recommendation serving

## 🔄 Supporting Capstone Goals

### 1. AI Music Recommender Agent
- **PostgreSQL**: Fast local prototyping of recommendation algorithms
- **Snowflake**: Scalable training data storage for ML models
- **Python**: Rich ML ecosystem for building recommendation engines

### 2. Real-time Recommendations
- **PostgreSQL**: Local caching of user preferences
- **Snowflake**: Historical analysis for improving recommendations
- **Python**: Async processing for real-time API responses

### 3. Multi-Source Data Integration
- **PostgreSQL**: Flexible staging for diverse music APIs
- **Snowflake**: Unified analytics across all music data sources
- **Python**: Universal API client capabilities

### 4. Scalability & Performance
- **PostgreSQL**: Efficient local development and testing
- **Snowflake**: Cloud-scale processing for production workloads
- **Python**: Proven performance for data-intensive applications

## 📊 Performance Considerations

### Local Development (PostgreSQL)
```
- Typical Query Response: <100ms
- JSON Operations: <50ms  
- Local Data Reload: <30 seconds
- Development Iteration: Fast & efficient
```

### Production Analytics (Snowflake)
```
- Complex Recommendation Queries: <2 seconds
- Batch ML Training: Minutes (not hours)
- Concurrent Users: 1000+ supported
- Data Loading: GB/minute throughput
```

### Python Processing
```
- API Collection: 100+ requests/minute (rate-limited)
- Data Transformation: MB/second processing
- ML Training: Leverages numpy/pandas optimizations
- Memory Efficiency: Polars for large datasets
```

## 🎯 Decision Matrix

| Requirement | PostgreSQL | Snowflake | Python | Alternative | Score |
|-------------|------------|-----------|--------|-------------|-------|
| Local Development | ✅ Excellent | ❌ Overkill | ✅ Excellent | SQLite: Limited | 9/10 |
| Cloud Scalability | ⚠️ Manual scaling | ✅ Auto-scale | ✅ Cloud-native | BigQuery: Vendor lock | 9/10 |
| Music API Integration | ✅ JSON support | ✅ VARIANT type | ✅ Rich ecosystem | Java: Verbose | 10/10 |
| ML/AI Development | ✅ SQL analytics | ✅ Built-in functions | ✅ Best-in-class | R: Limited deployment | 10/10 |
| Cost Efficiency | ✅ Free local | ✅ Pay-per-use | ✅ Open source | Commercial DBs: Expensive | 10/10 |
| Learning Value | ✅ Industry standard | ✅ Modern cloud | ✅ Data science standard | Niche tools: Limited transfer | 9/10 |

## 🚀 Future Considerations

### Scaling Paths
- **PostgreSQL**: Can migrate to cloud PostgreSQL services (AWS RDS, Google Cloud SQL)
- **Snowflake**: Already cloud-native, auto-scaling
- **Python**: Containerizable, serverless deployment ready

### Technology Evolution
- **PostgreSQL**: Vector extensions for music similarity search
- **Snowflake**: Native ML functions (coming features)
- **Python**: Continued ML library ecosystem growth

## 📝 Conclusion

Our technology stack is purpose-built for the **AI Music Recommender Agent**:

1. **PostgreSQL** provides reliable, flexible local development with production similarity
2. **Snowflake** offers cloud-scale analytics with built-in music data optimization
3. **Python** delivers the richest ecosystem for music APIs and ML development

This combination ensures we can **build locally, scale globally** while leveraging industry-standard tools that provide maximum learning value and career transferability.