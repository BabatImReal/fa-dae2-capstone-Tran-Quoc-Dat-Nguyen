
### Project Overview
- **Working title**: Health Data Pipeline
- **One-sentence summary**: An end-to-end health data pipeline that ingests both batch (Kaggle heart disease dataset) and streaming (Faker-generated hospital transaction) data, enabling analytics and real-time healthcare insights.
- **Business/value objective**: Provide healthcare analytics and operational insights by leveraging batch health survey data and real-time hospital transaction data.
- **Success metrics** (quantitative): Data pipeline reliability, data quality, analytics accuracy, and operational coverage.


### Problem & Scope
- **Problem statement and constraints**: Healthcare organizations require analytics on heart disease risk and hospital operations, but real streaming transaction data may not be available. The pipeline must support both batch analytics (from public health datasets) and real-time queries using fake hospital transaction data for development and demonstration.
- **Personas/stakeholders and primary use cases**: Healthcare analysts, hospital administrators, researchers. Use cases: analyze heart disease risk factors (batch), monitor hospital transactions and operations (streaming), validate data pipeline reliability.
- **In/out of scope**: In scope: health analytics, operational monitoring, batch and streaming data integration. Out of scope: patient care, medical diagnosis, real patient data.


### Data Sources
- **Batch source(s) (planned/production)**: [Kaggle Heart Disease UCI Dataset](https://www.kaggle.com/datasets/kamilpytlak/personal-key-indicators-of-heart-disease), CSV, ~320k rows, static snapshot.  
  See [batch-source-validation.md](docs/data-source/batch-source-validation.md) for validation details.
- **Streaming source(s)**: Fake hospital transaction data generated via Python scripts and Faker.  
  See [stream-source-validation.md](docs/data-source/stream-source-validation.md) for validation details.
- **Incremental strategy**: Use transaction IDs and timestamps for deduplication and incremental updates


### Architecture Overview
- **High-level diagram**: See [architecture.md](docs/architecture/architecture.md) for a detailed system diagram.
- **Data flow**: See [data-flow.md](docs/architecture/data-flow.md) for a description of how data moves from sources to databases.
- **Technology choices**: See [technology-decision.md](docs/architecture/technology-decision.md) for justification of the tech stack decisions.

### Data Modelling
- **Star Schema Model**: See [methodology.md](docs/data-modelling/methodology.md) for detailed data modelling explanation.
- **Entity Relationship Diagram (ERD)**: See [star-schema.png](docs/data-modelling/diagram/star-schema.png) for full ER Diagram.

## Project Setup

### Prerequisites
- Python 3.11 or higher
- uv (Python package manager)
- Docker and Docker Compose
- Git
- Snowflake account (optional for full pipeline)


## Running the Data Pipeline

### Complete Pipeline Execution (Step-by-Step)

Follow these steps in order to run the complete data pipeline from data collection to analytics:

#### Step 1: Clean Existing Data (Optional - Fresh Start)

```sql
-- Truncate raw data tables
TRUNCATE TABLE SC_RAW_DATA.OLIST_CUSTOMERS;
TRUNCATE TABLE SC_RAW_DATA.OLIST_GEOLOCATION;
TRUNCATE TABLE SC_RAW_DATA.OLIST_ORDER_ITEMS;
TRUNCATE TABLE SC_RAW_DATA.OLIST_ORDER_PAYMENTS;
TRUNCATE TABLE SC_RAW_DATA.OLIST_ORDER_REVIEWS;
TRUNCATE TABLE SC_RAW_DATA.OLIST_ORDERS;
TRUNCATE TABLE SC_RAW_DATA.OLIST_PRODUCTS;
TRUNCATE TABLE SC_RAW_DATA.OLIST_SELLERS;
TRUNCATE TABLE SC_RAW_DATA.PRODUCT_CATEGORY_NAME_TRANSLATION;

-- Truncate analytics tables
TRUNCATE TABLE SC_ANALYTICS.DIM_CUSTOMERS;
TRUNCATE TABLE SC_ANALYTICS.DIM_DATE;
TRUNCATE TABLE SC_ANALYTICS.DIM_ORDER_PAYMENT;
TRUNCATE TABLE SC_ANALYTICS.DIM_ORDER_REVIEWS;
TRUNCATE TABLE SC_ANALYTICS.DIM_PRODUCTS;
TRUNCATE TABLE SC_ANALYTICS.DIM_SELLERS;
TRUNCATE TABLE SC_ANALYTICS.FACT_ORDERS;

-- Remove stage files (if needed)
REMOVE @SC_RAW_DATA.CSV_STAGE;
```

#### Step 2: Collect Batch Data from Kaggle

```bash
# Download Brazilian E-Commerce dataset from Kaggle
uv run python scripts/ingestion/collect_batch_data.py
```

**Expected output:** CSV files downloaded to `data/batch/` directory

#### Step 3: Generate Fake Streaming Data

```bash
# Generate fake hospital/transaction data (JSON files)
uv run python scripts/ingestion/collect_fake_data.py
```

**Expected output:** JSON files created in `data/streaming/` directory

#### Step 4: Ingest Batch Data to Snowflake

```bash
# Load CSV batch files to Snowflake raw tables
uv run python scripts/ingestion/ingest_to_snowflake.py
```

**Expected output:** Data loaded into `SC_RAW_DATA.*` tables

#### Step 5: Start PostgreSQL (Docker)

```bash
# Start PostgreSQL container for streaming data
docker-compose up -d
```

**Verify:** `docker-compose ps` should show PostgreSQL running

#### Step 6: Ingest Streaming Data to PostgreSQL

```bash
# Load JSON streaming data to PostgreSQL
uv run python scripts/ingestion/ingest_to_postgres.py
```

**Expected output:** Data loaded into PostgreSQL staging tables

#### Step 7: Transfer PostgreSQL Data to Snowflake

```bash
# Transfer streaming data from PostgreSQL to Snowflake
uv run python scripts/ingestion/ingest_postgre_to_snowflake.py
```

**Expected output:** PostgreSQL data replicated to Snowflake

#### Step 8: Set Environment Variables for dbt

```bash
# Load environment variables (Linux/macOS)
set -a
source .env
set +a

# Or for Windows PowerShell:
# Get-Content .env | ForEach-Object {
#     if ($_ -match '^\s*([^#][^=]+)\s*=\s*(.+)\s*$') {
#         [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
#     }
# }
```

#### Step 9: Run dbt Transformations

```bash
# Navigate to dbt project directory
cd capstone_project

# Build all models (staging → dimensions → facts)
uv run dbt build

# Or run specific steps:
# uv run dbt run --select tag:staging     # Run staging models only
# uv run dbt run --select tag:dimension   # Run dimension models only
# uv run dbt run --select fact_orders     # Run fact table only
# uv run dbt test                          # Run all tests
```

**Expected output:**
- ✅ Staging models created in `SC_STAGING`
- ✅ Dimension tables created in `SC_ANALYTICS`
- ✅ Fact tables created in `SC_ANALYTICS`
- ✅ All tests passed (or warnings for known data quality issues)

---



### Implementation Milestones
- **Module 1 (Week 4)**: Data sources setup, basic pipeline structure
- **Module 2 (Week 4)**: Data warehouse, transformations, testing
- **Module 3 (Week 4)**: Real-time pipeline, orchestration
- **Module 4 (Week 4)**: AI agent implementation, RAG system, document processing
- **Module 5 (Week 4)**: Final testing, extra features, governance, demo prep