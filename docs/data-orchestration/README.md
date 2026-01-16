# Airflow Orchestration

This folder contains documentation for the Apache Airflow orchestration layer of the capstone project. Airflow is used to schedule and manage the data pipeline workflows.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           AIRFLOW ORCHESTRATION                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ┌───────────────────────┐         ┌───────────────────────┐                  │
│   │  batch_data_ingestion │────────▶│ batch_data_           │                  │
│   │                       │ trigger │ transformation        │                  │
│   │  • Extract from Kaggle│         │                       │                  │
│   │  • Load to Snowflake  │         │  • dbt snapshot       │                  │
│   │                       │         │  • dbt build          │                  │
│   └───────────────────────┘         └───────────────────────┘                  │
│         ⏰ Weekly                         🔗 Triggered                          │
│                                                                                 │
│   ┌───────────────────────┐                                                    │
│   │ capstone_db_          │                                                    │
│   │ connection_test       │                                                    │
│   │                       │                                                    │
│   │  • Test Snowflake     │                                                    │
│   │  • Test PostgreSQL    │                                                    │
│   └───────────────────────┘                                                    │
│         🖱️ Manual                                                              │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## DAGs Overview

| DAG | Schedule | Description | Trigger |
|-----|----------|-------------|---------|
| `batch_data_ingestion` | Weekly (Sun 2AM UTC) | Extracts data from Kaggle, loads to Snowflake | Scheduled |
| `batch_data_transformation` | None | Runs dbt snapshots and builds | Triggered by ingestion |
| `capstone_db_connection_test` | None | Tests database connections | Manual |

---

## DAG Details

### 1. batch_data_ingestion

**Purpose:** Collects batch data from Kaggle and ingests it into Snowflake's raw layer.

**Schedule:** `0 2 * * 0` (Every Sunday at 2:00 AM UTC)

**Tasks:**

```
extract_batch_data ──▶ load_to_snowflake ──▶ trigger_transformation
```

| Task | Description |
|------|-------------|
| `extract_batch_data` | Downloads Brazilian E-Commerce dataset from Kaggle |
| `load_to_snowflake` | Uploads CSV files to Snowflake stage and populates tables |
| `trigger_transformation` | Triggers the transformation DAG upon successful completion |

**Dependencies:**
- Kaggle credentials (`~/.kaggle/kaggle.json`)
- Snowflake connection (`snowflake_default`)

**Output:**
- Data loaded in `SC_RAW_DATA` schema

📁 See: [batch_data_ingestion.py](../../airflow/dags/batch_data_ingestion.py)

---

### 2. batch_data_transformation

**Purpose:** Transforms raw data using dbt, running snapshots and models in sequence.

**Schedule:** None (triggered by `batch_data_ingestion`)

**Tasks:**

```
dbt_snapshot ──▶ dbt_build
```

| Task | Description |
|------|-------------|
| `dbt_snapshot` | Runs `dbt deps` and `dbt snapshot` to capture SCD Type 2 dimensions |
| `dbt_build` | Runs `dbt build` to execute models and tests |

**Environment Variables:**

| Variable | Source |
|----------|--------|
| `SNOWFLAKE_ACCOUNT` | Airflow connection |
| `SNOWFLAKE_USER` | Airflow connection |
| `SNOWFLAKE_PRIVATE_KEY_FILE_PWD` | Airflow connection password |
| `SNOWFLAKE_ROLE` | Airflow connection extra |
| `SNOWFLAKE_WAREHOUSE` | Airflow connection extra |
| `SNOWFLAKE_DATABASE` | Airflow connection extra |
| `SNOWFLAKE_SCHEMA` | Airflow connection schema |
| `SNOWFLAKE_PRIVATE_KEY_FILE_PATH` | Airflow connection extra |
| `DBT_PROFILES_DIR` | `/opt/airflow/capstone_project/.dbt` |
| `DBT_PROJECT_DIR` | `/opt/airflow/capstone_project` |

**Input:**
- Raw data in `SC_RAW_DATA` schema

**Output:**
- Snapshots in `SNAPSHOTS` schema
- Staging models in `STAGING` schema
- Marts models in `ANALYTICS` schema

📁 See: [batch_data_transformation.py](../../airflow/dags/batch_data_transformation.py)

---

### 3. capstone_db_connection_test

**Purpose:** Validates database connections to PostgreSQL and Snowflake.

**Schedule:** None (manual trigger only)

**Tasks:**

```
test_snowflake_connection
test_postgres_connection
```
*(Tasks run in parallel)*

| Task | Description |
|------|-------------|
| `test_snowflake_connection` | Tests `snowflake_default` connection, returns Snowflake version |
| `test_postgres_connection` | Tests `postgres_kafka_default` connection |

**Use Cases:**
- Initial setup validation
- Troubleshooting connection issues
- Health checks

📁 See: [db_connection.py](../../airflow/dags/db_connection.py)

---

## Folder Structure

```
airflow/
├── dags/
│   ├── batch_data_ingestion.py      # Data extraction and loading
│   ├── batch_data_transformation.py # dbt transformation pipeline
│   ├── db_connection.py             # Connection testing DAG
│   └── __pycache__/                 # Python bytecode (gitignored)
├── config/
│   └── airflow.cfg                  # Airflow configuration
├── logs/                            # Task logs (gitignored)
├── plugins/                         # Custom Airflow plugins
├── setup/
│   ├── setup_airflow_postgres_connection.sh    # PostgreSQL connection setup
│   └── setup_airflow_snowflake_connection.sh   # Snowflake connection setup
└── Dockerfile.airflow               # Custom Airflow image
```

---

## How to Run

### Prerequisites

1. **Docker** installed and running
2. **Airflow connections** configured:
   - `snowflake_default` — Snowflake connection with private key auth
   - `postgres_kafka_default` — PostgreSQL connection

### Start Airflow

```bash
docker compose -f docker-compose-airflow.yml up -d
```

### Access Airflow UI

Open [http://localhost:8080](http://localhost:8080) in your browser.

Default credentials (check your `.env`):
- Username: `airflow`
- Password: `airflow`

### Trigger DAGs

**Option 1: Airflow UI**
1. Navigate to DAGs page
2. Click on the DAG name
3. Click "Trigger DAG" button

**Option 2: CLI**
```bash
# Trigger ingestion DAG
docker compose -f docker-compose-airflow.yml exec airflow-webserver \
    airflow dags trigger batch_data_ingestion

# Trigger transformation DAG (usually triggered by ingestion)
docker compose -f docker-compose-airflow.yml exec airflow-webserver \
    airflow dags trigger batch_data_transformation

# Test connections
docker compose -f docker-compose-airflow.yml exec airflow-webserver \
    airflow dags trigger capstone_db_connection_test
```

### View Logs

```bash
# View webserver logs
docker compose -f docker-compose-airflow.yml logs -f airflow-webserver

# View scheduler logs
docker compose -f docker-compose-airflow.yml logs -f airflow-scheduler

# View worker logs (if using CeleryExecutor)
docker compose -f docker-compose-airflow.yml logs -f airflow-worker
```

---

## Connection Setup

### Snowflake Connection

Run the setup script or manually configure:

```bash
./airflow/setup/setup_airflow_snowflake_connection.sh
```

**Manual setup via UI:**
1. Go to Admin → Connections
2. Add new connection:
   - **Conn Id:** `snowflake_default`
   - **Conn Type:** Snowflake
   - **Login:** `<your_user>`
   - **Password:** `<private_key_passphrase>`
   - **Schema:** `SC_RAW_DATA`
   - **Extra:**
     ```json
     {
       "account": "<your_account>",
       "warehouse": "<your_warehouse>",
       "database": "<your_database>",
       "role": "<your_role>",
       "private_key_file": "/path/to/rsa_key.p8"
     }
     ```

### PostgreSQL Connection

Run the setup script or manually configure:

```bash
./airflow/setup/setup_airflow_postgres_connection.sh
```

---

## Monitoring & Troubleshooting

### Check DAG Status

```bash
# List all DAGs
docker compose -f docker-compose-airflow.yml exec airflow-webserver \
    airflow dags list

# Check DAG state
docker compose -f docker-compose-airflow.yml exec airflow-webserver \
    airflow dags state batch_data_ingestion <execution_date>
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| DAG not appearing | Import error in DAG file | Check `airflow dags list-import-errors` |
| Connection failed | Missing/incorrect connection | Run connection test DAG, check credentials |
| dbt build failed | Missing dependencies | Check dbt logs, run `dbt deps` manually |
| Trigger failed | DAG paused or not found | Unpause DAG, check DAG ID spelling |

---

## Data Flow Summary

```
┌─────────┐    ┌─────────────────────┐    ┌──────────────────────┐    ┌───────────┐
│  Kaggle │───▶│ batch_data_ingestion│───▶│batch_data_           │───▶│ Snowflake │
│  (CSV)  │    │                     │    │transformation        │    │ (Analytics│
│         │    │ • Extract           │    │                      │    │  Layer)   │
│         │    │ • Load to Snowflake │    │ • dbt snapshot       │    │           │
│         │    │ • Trigger next DAG  │    │ • dbt build          │    │           │
└─────────┘    └─────────────────────┘    └──────────────────────┘    └───────────┘
                        │                          │
                        ▼                          ▼
                 ┌─────────────┐           ┌─────────────┐
                 │ SC_RAW_DATA │           │ SNAPSHOTS   │
                 │ (Raw Layer) │           │ STAGING     │
                 └─────────────┘           │ ANALYTICS   │
                                           └─────────────┘
```

---

*Last updated: December 2025*
