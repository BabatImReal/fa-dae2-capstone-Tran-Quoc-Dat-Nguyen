# Dagster vs Apache Airflow: Why Dagster for This Project

## Executive Summary

While both Dagster and Apache Airflow are powerful orchestration platforms, **Dagster's asset-centric design** makes it superior for modern data engineering projects that prioritize data lineage, quality, and analytics workflows.

---

## Three Fundamental Differences

### 1. **Asset-Native vs Task-Native Philosophy**

**Dagster** is **asset-native** — its primary abstraction is the **data asset itself** (a table, a model, a file). You define what data you want to produce, and Dagster figures out the tasks needed to create it.

**Airflow** is **task-native** — its primary abstraction is the **task** (a unit of work). You define what work to do, and can now declare what assets it produces.

**Result**: Dagster's worldview is intrinsically **data-centric**, while Airflow's is **operationally-centric** with data-awareness added on.

#### Code Comparison

**Dagster (Asset-First):**
```python
@asset(group_name="analytics")
def dim_customers(stg_customers: pd.DataFrame) -> pd.DataFrame:
    """Customer dimension - the asset IS the focus"""
    return transform_customers(stg_customers)
```

**Airflow (Task-First):**
```python
@task(outlets=[Dataset("dim_customers")])
def create_dim_customers():
    """Task to create customers - task IS the focus, asset is metadata"""
    data = extract()
    transformed = transform(data)
    load(transformed)
```

---

### 2. **Automatic vs Manual Lineage**

**Dagster**: Lineage is **automatic**. When you define an asset that depends on another, the lineage is instantly captured in a unified graph.

**Airflow**: You must **manually declare** lineage by specifying `inlets` and `outlets` for each task. This requires extra effort and is prone to being overlooked or misconfigured.

#### Lineage Comparison

**Dagster (Zero Configuration):**
```python
@asset
def raw_orders():
    return load_from_source()

@asset
def stg_orders(raw_orders):  # ← Dependency = Lineage (automatic)
    return clean(raw_orders)

@asset  
def fact_orders(stg_orders):  # ← Lineage graph built automatically
    return aggregate(stg_orders)
```
✅ **Lineage**: `raw_orders → stg_orders → fact_orders` (automatic)

**Airflow (Manual Configuration):**
```python
@task(outlets=[Dataset("raw_orders")])
def extract_orders():
    return load_from_source()

@task(
    inlets=[Dataset("raw_orders")],      # ← Must manually specify
    outlets=[Dataset("stg_orders")]      # ← Easy to forget or get wrong
)
def stage_orders():
    return clean(read_data())

@task(
    inlets=[Dataset("stg_orders")],      # ← Repetitive declaration
    outlets=[Dataset("fact_orders")]     # ← No automatic enforcement
)  
def create_fact():
    return aggregate(read_data())
```
⚠️ **Lineage**: Must manually declare for every task, prone to errors

---

### 3. **Native dbt Integration vs Orchestration**

**Dagster's integration** understands your dbt project **natively**. It automatically ingests your dbt manifest and displays every model, source, and test as a first-class asset in its graph with **no extra code**.

**Airflow's integration** orchestrates dbt runs. It excels at running the `dbt run` command as a task within a workflow, but the deep, **model-level visibility and lineage** is not inherent and requires more setup to achieve.

#### dbt Integration Comparison

**Dagster (Model-Level Visibility):**
```python
@dbt_assets(
    manifest=project_root / "dbt_project" / "target" / "manifest.json",
    dagster_dbt_translator=CustomDbtTranslator(),
)
def dbt_analytics_models(context, dbt: DbtCliResource):
    yield from dbt.cli(["build"], context=context).stream()
```

**What you get automatically:**
- ✅ Every dbt model appears as a separate asset (`stg_orders`, `dim_customers`, `fact_orders`)
- ✅ Full lineage: `stg_orders → int_order_items → fact_orders`
- ✅ dbt tests become Dagster asset checks
- ✅ Run individual models from UI
- ✅ Column-level lineage (with metadata)

**Airflow (Task-Level Orchestration):**
```python
dbt_run = DbtRunOperator(
    task_id="dbt_run",
    project_dir="/dbt",
)
```

**What you get:**
- ⚠️ `dbt run` is a single monolithic task
- ⚠️ No visibility into individual models
- ⚠️ Can't run specific models without creating separate tasks
- ⚠️ Lineage requires parsing manifest separately
- ⚠️ Tests are separate tasks

---

## Quick Comparison Table

| Feature | Dagster | Airflow |
|---------|---------|---------|
| **Primary Abstraction** | Data Asset | Task/DAG |
| **Lineage** | Automatic | Manual (`inlets`/`outlets`) |
| **dbt Integration** | Native (model-level) | Orchestration (task-level) |
| **Local Development** | `dagster dev` (instant) | Docker setup required |
| **Testing** | First-class asset checks | Manual task testing |
| **Type Safety** | Strong (Pydantic) | Weak |
| **Data Previews** | Built-in | Custom implementation |
| **Best For** | Data pipelines & analytics | Operational workflows |

---

## Why Dagster for This Capstone Project

### ✅ **Project Requirements**

1. **18 dbt models** with complex dependencies
   - **Need**: Model-level lineage and selective execution
   - **Dagster**: ✅ Native support, every model is an asset
   - **Airflow**: ⚠️ Single task, no granular control

2. **Multiple data sources** (Batch + Streaming)
   - **Need**: Different refresh schedules, clear lineage
   - **Dagster**: ✅ Asset-based scheduling, automatic lineage
   - **Airflow**: ⚠️ Separate DAGs, manual lineage declaration

3. **Data quality focus**
   - **Need**: Built-in testing and validation
   - **Dagster**: ✅ Asset checks, automatic metadata
   - **Airflow**: ⚠️ Manual quality checks as tasks

4. **Local development workflow**
   - **Need**: Test before deployment
   - **Dagster**: ✅ `dagster dev` for instant testing
   - **Airflow**: ⚠️ Requires full Docker environment

---

## Validation: Your Assessment Was Correct ✅

Your three-point comparison is **accurate and well-articulated**:

1. **✅ Asset-native vs Task-native**: This is the fundamental philosophical difference that cascades into everything else.

2. **✅ Automatic vs Manual lineage**: Dagster's built-in lineage saves significant effort and prevents configuration drift.

3. **✅ Native dbt integration vs Orchestration**: Dagster treats dbt models as first-class citizens; Airflow treats dbt as a command to execute.

**Your analysis demonstrates strong understanding** of both tools and correctly identifies why Dagster aligns better with modern analytics engineering practices.

---

## Architecture in This Project

```
┌─────────────────────────────────────────────────────────┐
│              Dagster Asset-Centric Pipeline              │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Assets (Data) ───────────► Automatic Lineage           │
│                                                          │
│  batch_csv_files ──────────► snowflake_raw_batch_data   │
│  postgres_user_events ─────► snowflake_streaming_data   │
│  stg_orders ───────────────► dim_customers               │
│  stg_products ─────────────► dim_products                │
│  dim_customers + stg_orders ► fact_orders                │
│                                                          │
│  🎯 Focus: "What data exists and how is it related?"    │
└─────────────────────────────────────────────────────────┘

vs

┌─────────────────────────────────────────────────────────┐
│              Airflow Task-Centric Pipeline               │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Tasks (Work) ───────────► Manual Lineage Required      │
│                                                          │
│  download_csvs ────────────► upload_to_snowflake        │
│  check_postgres ───────────► load_to_snowflake          │
│  dbt_run (all models) ────► dbt_test                    │
│                                                          │
│  ⚠️ Focus: "What work needs to be done and in what     │
│     order?"                                             │
└─────────────────────────────────────────────────────────┘
```

---

## Conclusion

**Choose Dagster** for data pipelines where:
- **Data assets** are the primary concern
- **Lineage** must be accurate and automatic
- **dbt** is a core component
- **Testing & quality** are priorities
- **Modern data stack** is in use

**Choose Airflow** for operational workflows where:
- **Task orchestration** is primary
- **Legacy integrations** are needed
- **Operational processes** dominate over data assets

**For this capstone project**: Dagster is the clear choice due to heavy dbt usage, complex data lineage requirements, and focus on analytics engineering best practices.

---

**Document Version**: 2.0 (Condensed)  
**Last Updated**: November 7, 2025

