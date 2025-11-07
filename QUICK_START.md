# 🚀 Quick Start Commands

## Prerequisites
```bash
# Ensure you're in the project root
cd d:/Data/Foundry_AI/projects/fa-dae2-capstone-Tran-Quoc-Dat-Nguyen

# Start PostgreSQL
docker-compose up -d
```

---

## Option 1: Run dlt Standalone (Recommended First)

```bash
# Test the dlt pipeline independently
uv run python scripts/ingestion/dlt_postgres_to_snowflake.py
```

**Expected Output:**
```
🚀 Starting dlt pipeline: PostgreSQL → Snowflake
📊 Loading from staging.user_events to SC_RAW_DATA.RAW_DATA_POSTGRE
✅ Pipeline completed successfully!
📈 Loaded X rows
```

---

## Option 2: Run via Dagster UI

```bash
# Start Dagster web server
cd dagster-orchestrator
uv run dagster dev
```

Then open **http://localhost:3000** and:
1. Click **"Assets"** tab
2. Select `snowflake_streaming_data`
3. Click **"Materialize"**

---

## Common Commands

### View Dagster Assets
```bash
cd dagster-orchestrator
uv run dagster asset list
```

### Materialize Specific Asset (CLI)
```bash
cd dagster-orchestrator
uv run dagster asset materialize --select snowflake_streaming_data
```

### Materialize Asset Group
```bash
cd dagster-orchestrator
uv run dagster asset materialize --select "batch_ingestion*"
```

### Check dlt Pipeline State
```python
import dlt
pipeline = dlt.pipeline('postgres_to_snowflake')
print(pipeline.state)
```

### Verify Setup
```bash
uv run python test_dagster_setup.py
```

---

## Troubleshooting

### Cannot import dlt
```bash
# Always use uv run
uv run python your_script.py
```

### PostgreSQL not running
```bash
docker-compose up -d
docker-compose ps  # Check status
```

### Dagster UI not loading
```bash
# Ensure you're in dagster-orchestrator directory
cd dagster-orchestrator
uv run dagster dev
```

---

## 📖 Full Documentation

- **Complete Setup Guide**: `dagster-orchestrator/SETUP_GUIDE.md`
- **dlt + Dagster Summary**: `DLT_DAGSTER_SUMMARY.md`
- **Project README**: `README.md`
