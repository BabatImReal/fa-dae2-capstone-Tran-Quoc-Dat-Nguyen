🏗️ **IMPLEMENTATION PLAN**

---

### M01 W04: Foundation (Current Focus)
**Goal:** Working mini pipeline with both batch and real-time processing

#### Real-time Pipeline
- **Source:** Fake data stream (Python + Faker)
- **Process:** Row-by-row data collection
- **Destination:** PostgreSQL (via Docker)
- **Scripts:** `ingestion/collect_realtime.py`, `ingestion/load_to_postgres.py`

#### Batch Pipeline
- **Source:** Kaggle Spotify Tracks Dataset (CSV)
- **Process:** Bulk data collection (500+ rows)
- **Destination:** Snowflake
- **Scripts:** `ingestion/collect_batch.py`, `ingestion/load_to_snowflake.py`

> **Note:** Two different data sources are used—one for each pipeline type.

---

### M02 W04: Data Processing (Future Planning)
- dbt transformations and data modeling
- Data quality testing and validation
- Warehouse structure optimization

---

### M03 W04: Real-time & Orchestration (Future Planning)
- Kafka streaming implementation
- Airflow pipeline orchestration
- End-to-end data flow automation

---

### M04 W04: AI Agent (Future Planning)
- LangGraph agent development
- RAG system with document processing
- Natural language data querying

---

### M05 W04: Final Integration (Future Planning)
- System testing and validation
- Performance optimization
- Demo preparation and documentation
