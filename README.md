
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

## Project Setup

### Prerequisites
- Python 3.11 or higher
- uv (Python package manager)
- Docker and Docker Compose
- Git
- Snowflake account (optional for full pipeline)


### 1. Environment Setup

#### Install uv (if not already installed)
```bash
# On Windows:
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# On Linux/macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip:
pip install uv
```

#### Clone and Navigate to Project
```bash
git clone <repository-url>
cd fa-dae2-capstone-Tran-Quoc-Dat-Nguyen
```

#### Install Dependencies with uv
```bash
# Sync all dependencies (creates virtual environment automatically)
uv sync

# Install development dependencies
uv sync --group dev

# Or install all groups
uv sync --all-groups
```


### 2. Environment Variables Configuration

#### Copy Environment Template
```bash
cp config/env_example.txt .env
```

#### Update .env File
Edit the `.env` file with your specific configuration

#### Load Environment Variables
```bash
# Load environment variables
export $(cat .env | xargs)
```


### 3. Docker Setup

#### Create Docker Network
```bash
# Create the required Docker network
docker network create fa-dae2-capstone_kafka_network
```

#### Start PostgreSQL with Docker Compose
```bash
# Start PostgreSQL service
docker-compose up -d postgres

# Check if PostgreSQL is running
docker-compose ps

# View logs
docker-compose logs postgres
```

#### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ This will delete all data)
docker-compose down -v
```


### 4. PostgreSQL Setup

#### Database Initialization
The PostgreSQL database is automatically initialized with the schema defined in `postgres-lab/sql/init.sql` when the container starts.

#### Connect to PostgreSQL
```bash
# Connect using psql (if installed locally)
psql -h localhost -p 5432 -U staging_user -d staging_db

# Or connect via Docker
docker exec -it m01w02-postgres psql -U staging_user -d staging_db
```

#### Verify Database Setup
```sql
-- List all tables
\dt

-- Check table structure
\d table_name

-- Exit psql
\q
```


### 5. Snowflake Setup (Optional)

#### Database Structure
Create the following structure in your Snowflake account:

```sql
-- Create database
CREATE DATABASE IF NOT EXISTS HEALTH_PIPELINE;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS HEALTH_PIPELINE.RAW_DATA;
CREATE SCHEMA IF NOT EXISTS HEALTH_PIPELINE.STAGING;
CREATE SCHEMA IF NOT EXISTS HEALTH_PIPELINE.ANALYTICS;

-- Grant permissions (adjust role as needed)
GRANT USAGE ON DATABASE HEALTH_PIPELINE TO ROLE your_role;
GRANT USAGE ON ALL SCHEMAS IN DATABASE HEALTH_PIPELINE TO ROLE your_role;
GRANT CREATE TABLE ON ALL SCHEMAS IN DATABASE HEALTH_PIPELINE TO ROLE your_role;
```


#### Authentication Setup

**Option 1: Username/Password**
- Use the `SNOWFLAKE_USER` and `SNOWFLAKE_PASSWORD` variables in your `.env` file

**Option 2: Private Key (Recommended)**
1. Generate a private key pair:
  ```bash
  # Generate private key
  openssl genrsa 2048 | openssl pkcs8 -topk8 -inform PEM -out rsa_key.p8 -nocrypt
   
  # Generate public key
  openssl rsa -in rsa_key.p8 -pubout -out rsa_key.pub
  ```

2. Add the public key to your Snowflake user:
  ```sql
  ALTER USER your_username SET RSA_PUBLIC_KEY='your_public_key_content';
  ```

3. Update your `.env` file with the private key path and passphrase


### 6. Testing the Setup

#### Test Database Connections
```bash
# Test PostgreSQL and Snowflake connections
uv run python tests/test_connection.py
```

#### Test Data Pipeline
```bash
# Run ingestion tests
uv run python tests/test_ingestion.py

# Run full pipeline test
uv run python tests/test_data_pipeline.py
```

#### Run All Tests
```bash
# Run all tests with pytest
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v
```


### 7. Running the Pipeline

#### Collect and Ingest Data
```bash
# Collect batch data (heart disease)
uv run python scripts/ingestion/collect_batch_data.py

# Generate fake hospital transaction streaming data
uv run python scripts/ingestion/collect_fake_data.py

# Ingest to PostgreSQL
uv run python scripts/ingestion/ingest_to_postgre.py

# Ingest to Snowflake (if configured)
uv run python scripts/ingestion/ingest_to_snowflake.py

# Transfer from PostgreSQL to Snowflake
uv run python scripts/ingestion/ingest_postgre_to_snowflake.py
```

#### Run Main Pipeline
```bash
uv run python main.py
```


### 8. Troubleshooting

#### Common Issues

**Docker Issues:**
- Ensure Docker Desktop is running
- Check if port 5432 is already in use: `netstat -an | grep 5432`
- Reset Docker network: `docker network rm fa-dae2-capstone_kafka_network && docker network create fa-dae2-capstone_kafka_network`

**PostgreSQL Connection Issues:**
- Verify environment variables are loaded: `echo $POSTGRES_USER`
- Check container logs: `docker-compose logs postgres`
- Ensure database is healthy: `docker-compose ps`

**Snowflake Connection Issues:**
- Verify account identifier format (should include region)
- Check private key format and permissions
- Ensure role has necessary privileges
- Test connection with Snowflake's web interface first

**Python Environment Issues:**
- Verify uv installation: `uv --version`
- Check Python version: `uv python list`
- Reinstall dependencies: `uv sync --reinstall`
- Use uv to run commands: `uv run python script.py`

#### Getting Help
- Check application logs in the console output
- Review Docker logs: `docker-compose logs`
- Verify environment variables: `cat .env`
- Test individual components using the test scripts


### Implementation Milestones
- **Module 1 (Week 4)**: Data sources setup, basic pipeline structure
- **Module 2 (Week 4)**: Data warehouse, transformations, testing
- **Module 3 (Week 4)**: Real-time pipeline, orchestration
- **Module 4 (Week 4)**: AI agent implementation, RAG system, document processing
- **Module 5 (Week 4)**: Final testing, extra features, governance, demo prep