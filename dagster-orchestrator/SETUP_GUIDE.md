# Dagster Orchestrator Setup Guide

## 📋 Overview

This Dagster orchestrator manages the complete data pipeline:
- **Batch Ingestion**: Kaggle Brazilian E-Commerce dataset → Snowflake
- **Streaming Ingestion**: Kafka → PostgreSQL → Snowflake (using dlt)
- **Transformations**: dbt models (staging → dimensions → facts)

## 🎯 **Why dlt for PostgreSQL → Snowflake?**

**YES, dlt CAN and SHOULD be used!** Here's why:

✅ **Incremental Loading**: Automatically tracks state and loads only new records  
✅ **Schema Evolution**: Auto-detects schema changes  
✅ **Error Handling**: Built-in retry logic and error recovery  
✅ **Data Quality**: Type conversion and validation  
✅ **Performance**: Efficient bulk loading to Snowflake  
✅ **Simplicity**: Replaces 100+ lines of pandas code with ~20 lines  
✅ **Dagster Integration**: Native support via `dagster-embedded-elt`  

---

## 🚀 Installation Steps

### Step 1: Install Dependencies

From the **project root** directory:

```bash
# Install all project dependencies (including dlt and Dagster)
uv pip install -e .

# OR install just the dagster-orchestrator package
cd dagster-orchestrator
uv pip install -e ".[dev]"
```

This installs:
- `dagster` - Core orchestration framework
- `dagster-webserver` - Web UI
- `dagster-dbt` - dbt integration
- `dagster-embedded-elt` - ELT integrations
- `dlt[snowflake,postgres]` - Data Load Tool with connectors
- All other database drivers and utilities

### Step 2: Verify Environment Variables

Ensure your `.env` file in the **project root** contains:

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=capstone
POSTGRES_USER=staging_user
POSTGRES_PASSWORD=your_password

# Snowflake
SNOWFLAKE_ACCOUNT=your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_WAREHOUSE=your_warehouse
SNOWFLAKE_DATABASE=your_database
SNOWFLAKE_SCHEMA=SC_RAW_DATA
SNOWFLAKE_ROLE=your_role
SNOWFLAKE_AUTHENTICATOR=SNOWFLAKE_JWT
SNOWFLAKE_PRIVATE_KEY_FILE_PATH=./rsa_key.pem
SNOWFLAKE_PRIVATE_KEY_FILE_PWD=your_key_password

# Kafka (optional)
KAFKA_BOOTSTRAP_SERVERS=localhost:29092
KAFKA_TOPIC=user_events
```

### Step 3: Verify dlt Installation

```bash
# Test dlt
python -c "import dlt; print(f'dlt version: {dlt.__version__}')"

# Expected output: dlt version: 1.5.x
```

---

## 🏃 Running the Dagster Orchestrator

### Option 1: Dagster Web UI (Recommended)

```bash
# From the dagster-orchestrator directory
cd dagster-orchestrator

# Start Dagster web server
dagster dev
```

Then open your browser to **http://localhost:3000**

You'll see:
- **Asset Catalog**: All data assets and their dependencies
- **Lineage Graph**: Visual data flow from source to analytics
- **Run History**: Past pipeline executions
- **Asset Materialization**: Click to run individual assets or full pipeline

### Option 2: CLI Execution

```bash
# Materialize all assets
dagster asset materialize --select "*"

# Materialize specific asset groups
dagster asset materialize --select "batch_ingestion"
dagster asset materialize --select "streaming_ingestion"

# Materialize a specific asset
dagster asset materialize --select "snowflake_streaming_data"
```

### Option 3: Python Script

```python
from dagster import materialize
from dagster_orchestrator.definitions import defs

# Materialize all assets
result = materialize(
    assets=defs.get_all_asset_specs(),
    resources=defs.resources,
)
```

---

## 📊 Understanding the Assets

### 1. **batch_csv_files**
- **What**: Downloads Brazilian E-Commerce data from Kaggle
- **When**: Run manually or on schedule
- **Output**: CSV files in `data/external/`

### 2. **snowflake_raw_batch_data**
- **What**: Uploads CSVs to Snowflake staging and loads to raw tables
- **Depends on**: `batch_csv_files`
- **Output**: Tables in `SC_RAW_DATA` schema

### 3. **postgres_user_events**
- **What**: Observes PostgreSQL table (populated by Kafka consumer)
- **When**: Run to check current state
- **Output**: Metadata about row counts

### 4. **snowflake_streaming_data** ⭐ **dlt-powered**
- **What**: Incrementally loads data from PostgreSQL to Snowflake using **dlt**
- **Depends on**: `postgres_user_events`
- **How**: 
  - Uses dlt's `sql_table` source
  - Tracks state via `ingested_at` timestamp
  - Only loads new records (incremental)
  - Auto-creates Snowflake table if missing
- **Output**: `SC_RAW_DATA.RAW_DATA_POSTGRE` table

---

## 🔧 dlt Configuration Details

### How dlt Works in This Pipeline

1. **Source**: PostgreSQL `staging.user_events` table
2. **Destination**: Snowflake `SC_RAW_DATA.RAW_DATA_POSTGRE` table
3. **Incremental Column**: `ingested_at` timestamp
4. **Write Mode**: `append` (adds new rows only)

### dlt State Management

dlt automatically stores state in:
- **Location**: `~/.dlt/pipelines/postgres_to_snowflake/`
- **Purpose**: Tracks last loaded timestamp to enable incremental loads

### dlt vs. Manual Pandas Approach

| Feature | Manual (Old) | dlt (New) |
|---------|-------------|----------|
| Code Lines | ~150 | ~20 |
| Incremental Logic | Manual tracking | Automatic |
| Error Handling | Manual try/catch | Built-in retry |
| Schema Changes | Manual ALTER TABLE | Auto-detected |
| Performance | Row-by-row inserts | Bulk loading |
| State Management | External database | Built-in |

---

## 🧪 Testing the dlt Pipeline

### Test 1: Standalone dlt Script

```bash
# Run the standalone dlt script
cd scripts/ingestion
python dlt_postgres_to_snowflake.py
```

Expected output:
```
🚀 Starting dlt pipeline: PostgreSQL → Snowflake
📊 Loading from staging.user_events to SC_RAW_DATA.RAW_DATA_POSTGRE
✅ Pipeline completed successfully!
📈 Loaded X new rows
```

### Test 2: Via Dagster

```bash
# Start Dagster UI
cd dagster-orchestrator
dagster dev

# In the UI:
# 1. Go to Assets
# 2. Click "snowflake_streaming_data"
# 3. Click "Materialize"
# 4. Watch the logs
```

### Test 3: Verify Incremental Loading

```bash
# 1. Run pipeline first time (loads all data)
python scripts/ingestion/dlt_postgres_to_snowflake.py

# 2. Add new data to PostgreSQL
python kafka/kafka_producer.py  # Let it run for 30 seconds

# 3. Run pipeline again (loads only new data)
python scripts/ingestion/dlt_postgres_to_snowflake.py

# Expected: Only new rows loaded (not full dataset)
```

---

## 📅 Scheduling (Optional)

Create scheduled runs in Dagster:

```python
# In dagster_orchestrator/schedules.py
from dagster import schedule, RunRequest, ScheduleDefinition

@schedule(
    cron_schedule="0 * * * *",  # Every hour
    job_name="streaming_ingestion_job",
)
def hourly_streaming_schedule():
    return RunRequest()

@schedule(
    cron_schedule="0 2 * * *",  # Daily at 2 AM
    job_name="batch_ingestion_job",
)
def daily_batch_schedule():
    return RunRequest()
```

---

## 🔍 Monitoring & Debugging

### View dlt Logs

```bash
# Check dlt pipeline state
python -c "
import dlt
pipeline = dlt.pipeline('postgres_to_snowflake')
print(pipeline.state)
"
```

### View Dagster Logs

- **UI**: Check "Run Details" for each asset materialization
- **CLI**: Logs appear in terminal when running `dagster dev`

### Common Issues

**Issue 1: dlt import error**
```bash
# Solution: Install dlt with extras
uv pip install "dlt[snowflake,postgres]"
```

**Issue 2: Snowflake authentication fails**
```bash
# Solution: Verify private key path and permissions
ls -la rsa_key.pem
# Should be readable by current user
```

**Issue 3: No new data loaded**
```bash
# This is normal if PostgreSQL has no new records!
# dlt tracks state and only loads incremental data
```

---

## 📚 Next Steps

1. ✅ **Test dlt pipeline** standalone
2. ✅ **Run via Dagster UI** to see asset lineage
3. ⏭️ **Add dbt assets** (uncomment in `assets.py`)
4. ⏭️ **Create schedules** for automation
5. ⏭️ **Add data quality checks** as assets
6. ⏭️ **Set up alerting** for pipeline failures

---

## 🎯 Benefits Summary

Using dlt with Dagster gives you:

1. **Automatic Incremental Loading** - No manual state tracking
2. **Data Lineage Visualization** - See full pipeline in Dagster UI
3. **Retry Logic** - Auto-retry on transient failures
4. **Schema Evolution** - Auto-adapt to table changes
5. **Performance** - Efficient bulk loading
6. **Observability** - Track metrics, logs, and run history
7. **Modularity** - Each step is a testable asset

---

## 📞 Support

For issues or questions:
- Check Dagster logs in the UI
- Review dlt documentation: https://dlthub.com/docs
- Verify environment variables in `.env`
- Test database connections independently

---

**Happy Orchestrating! 🚀**
