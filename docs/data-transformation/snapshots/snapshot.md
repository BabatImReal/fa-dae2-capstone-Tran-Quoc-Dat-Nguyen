# Snapshot Layer

The **Snapshot Layer** captures historical changes to source data using **dbt snapshots** with **SCD Type 2** (Slowly Changing Dimension Type 2) strategy.

---

## Purpose

- **Track changes** to slowly changing dimensions over time
- **Maintain full history** of record modifications
- **Enable point-in-time analysis** (e.g., "What was the customer's address on 2023-01-15?")
- **Audit trail** for compliance and debugging

---

## SCD Type 2 Strategy

When a record changes in the source, dbt snapshots:
1. **Expire** the old record by setting `dbt_valid_to` to the current timestamp
2. **Insert** a new record with the updated values and `dbt_valid_to = NULL`

| Column | Description |
|--------|-------------|
| `dbt_scd_id` | Unique identifier for each version of the record |
| `dbt_updated_at` | Timestamp when the snapshot detected this version |
| `dbt_valid_from` | Timestamp when this version became active |
| `dbt_valid_to` | Timestamp when this version expired (NULL = current) |

---

## Snapshot Tables

| Snapshot | Source Table | Unique Key | Strategy | Check Columns |
|----------|--------------|------------|----------|---------------|
| `customers_snapshot` | `sc_raw_data.olist_customers` | `customer_id` | `check` | All columns |
| `orders_snapshot` | `sc_raw_data.olist_orders` | `order_id` | `check` | All columns |
| `order_items_snapshot` | `sc_raw_data.olist_order_items` | `order_id, order_item_id` | `check` | All columns |
| `order_payments_snapshot` | `sc_raw_data.olist_order_payments` | `order_id, payment_sequential` | `check` | All columns |
| `order_reviews_snapshot` | `sc_raw_data.olist_order_reviews` | `review_id` | `check` | All columns |
| `products_snapshot` | `sc_raw_data.olist_products` | `product_id` | `check` | All columns |
| `sellers_snapshot` | `sc_raw_data.olist_sellers` | `seller_id` | `check` | All columns |

---

## Example: Customer Snapshot

**Snapshot definition** (`snapshots/customer_snapshot.sql`):

```sql
{% snapshot customers_snapshot %}

{{
    config(
        target_schema='snapshots',
        unique_key='customer_id',
        strategy='check',
        check_cols='all'
    )
}}

SELECT * FROM {{ source('sc_raw_data', 'olist_customers') }}

{% endsnapshot %}
```

**Sample output:**

| customer_id | customer_city | dbt_valid_from | dbt_valid_to |
|-------------|---------------|----------------|--------------|
| c001 | São Paulo | 2023-01-01 | 2023-06-15 |
| c001 | Rio de Janeiro | 2023-06-15 | NULL |

In this example, customer `c001` moved from São Paulo to Rio de Janeiro on 2023-06-15.

---

## Running Snapshots

```bash
# Run all snapshots
dbt snapshot

# Run specific snapshot
dbt snapshot --select customers_snapshot

# Run snapshots with full refresh (caution: loses history)
dbt snapshot --full-refresh
```

---

## Best Practices

1. **Run snapshots regularly** (e.g., daily) to capture changes
2. **Never run with `--full-refresh`** in production (loses history)
3. **Use `check` strategy** for comprehensive change detection
4. **Use `timestamp` strategy** if source has a reliable `updated_at` column
5. **Monitor snapshot growth** to manage storage costs

---

## Data Flow

```
┌─────────────────┐         ┌──────────────────────┐         ┌─────────────────┐
│   SOURCE TABLE  │         │   SNAPSHOT TABLE     │         │  STAGING MODEL  │
│                 │         │                      │         │                 │
│  olist_customers│───CDC──▶│  customers_snapshot  │────────▶│  stg__customers │
│                 │         │  (with SCD2 columns) │         │                 │
└─────────────────┘         └──────────────────────┘         └─────────────────┘
```

---

*Last updated: December 2025*
