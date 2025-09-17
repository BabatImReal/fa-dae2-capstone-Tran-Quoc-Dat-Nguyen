### Project Overview
- **Working title**: AI Music Recommender Agent
- **One-sentence summary**: An AI agent that recommends songs by genre or tracks by artist, using a limited dataset or the Spotify API for real-time search and metadata enrichment.
- **Business/value objective**: Enable users to discover music tailored to their preferences, leveraging both curated datasets and live Spotify data for richer recommendations and insights.
- **Success metrics** (quantitative): Recommendation accuracy, user engagement rate, API response time, coverage of genres/artists.
- **Architecture foundation**: Built on [data engineering fundamentals](architecture/data-engineering-fundamentals.md) - answering the five core questions of modern data systems.

### Problem & Scope
- **Problem statement and constraints**: Users need personalized music recommendations and artist/song information, but may be limited by dataset scope or require real-time data. Must handle both batch and streaming sources, and support flexible queries.
- **Personas/stakeholders and primary use cases**: Music listeners, playlist curators, researchers. Use cases: recommend a song by genre, find a track by artist, retrieve artist/song metadata (followers, tracks, albums, etc.).
- **In/out of scope**: In scope: recommendations, metadata lookup, batch and API integration. Out of scope: audio playback, user authentication, social features.

### Data Sources
- **Batch source(s)**: [Kaggle Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset), CSV, ~230k tracks, static snapshot (last updated 2023)
- **Streaming source(s)**: Spotify API (https://api.spotify.com/v1/), JSON, real-time queries, up to 20 requests/sec
- **Incremental strategy**: Use track/artist IDs and timestamps for deduplication and incremental updates

### High-Level Architecture
- **Diagram link or embed placeholder**: See [complete architecture documentation](architecture/architecture.md)
- **Components**: 
  - **Ingestion** (How does it move?): batch (CSV), stream (API)
  - **Storage** (Where do we store it?): PostgreSQL (staging), Snowflake (analytics)
  - **Transform** (How do we process it?): dbt for batch data cleaning/enrichment
  - **Orchestration**: Airflow for scheduled jobs
  - **Agent** (How do we use it?): AI recommender (tools/RAG)
- **Data flow**: 
  1. **Extract**: Data is ingested from batch sources (CSV dataset) and streaming sources (Spotify API).
  2. **Load**: Raw data is stored in PostgreSQL (local staging) and Snowflake (cloud warehouse).
  3. **Transform**: Transformation processes (dbt) clean and enrich the data in Snowflake.
  4. **Analytics**: Processed data is made available for analysis and querying.
  5. **AI Layer**: The AI agent accesses the processed data to generate recommendations or retrieve metadata.
  6. **Output**: Results are returned to the user or downstream applications.
- **Pattern**: ELT (Extract, Load, Transform) with OLTP staging and OLAP analytics

### Implementation Milestones
- **Module 1 (Week 4)**: Data sources setup, basic pipeline structure
- **Module 2 (Week 4)**: Data warehouse, transformations, testing
- **Module 3 (Week 4)**: Real-time pipeline, orchestration
- **Module 4 (Week 4)**: AI agent implementation, RAG system, document processing
- **Module 5 (Week 4)**: Final testing, extra features, governance, demo prep