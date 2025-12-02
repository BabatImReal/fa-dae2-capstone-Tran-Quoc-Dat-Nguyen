# Staging Layer (Bronze)

The **Staging Layer** is the first transformation layer after snapshots. It performs light transformations to clean and standardize raw data without applying business logic.

---

## Purpose

- **Type casting** — Convert strings to appropriate data types (dates, integers, decimals)
- **Column renaming** — Standardize naming conventions (snake_case)
- **Null handling** — Apply default values or coalesce nulls
- **Basic cleaning** — Trim whitespace, lowercase text, remove duplicates
- **1:1 mapping** — Each staging model maps to exactly one source/snapshot table

---

## What Staging Does NOT Do

❌ No business logic or calculations  
❌ No joins between tables  
❌ No aggregations  
❌ No derived columns based on business rules  

These transformations belong in the **Intermediate** or **Analytics** layers.

---

## Staging Models

| Model | Source | Description |
|-------|--------|-------------|
| `stg__customers` | `customers_snapshot` | Customer base with cleaned geography |
| `stg__orders` | `orders_snapshot` | Order headers with parsed timestamps |
| `stg__order_items` | `order_items_snapshot` | Line items with typed prices |
| `stg__order_payments` | `order_payments_snapshot` | Payments with typed amounts |
| `stg__order_reviews` | `order_reviews_snapshot` | Reviews with typed scores |
| `stg__products` | `products_snapshot` | Products with typed dimensions |
| `stg__sellers` | `sellers_snapshot` | Sellers with cleaned location |
| `stg__product_category_name_translation` | `product_category_name_translation` | Category name mappings |

---

## Example: Staging Customers

**Source data (snapshot):**

| customer_id | customer_zip_code_prefix | customer_city | customer_state |
|-------------|--------------------------|---------------|----------------|
| c001 | 01310 | são paulo | SP |
| c002 | 22041 | rio de janeiro | RJ |

**Staging model** (`models/staging/stg__customers.sql`):

```sql
WITH source AS (
    SELECT * FROM {{ ref('customers_snapshot') }}
    WHERE dbt_valid_to IS NULL  -- Get current records only
),

staged AS (
    SELECT
        -- Primary key
        customer_id,
        
        -- Type casting and cleaning
        CAST(customer_zip_code_prefix AS INTEGER) AS customer_zip_code,
        TRIM(INITCAP(customer_city)) AS customer_city,
        UPPER(customer_state) AS customer_state,
        
        -- Metadata
        dbt_valid_from AS _loaded_at
        
    FROM source
)

SELECT * FROM staged
```

**Staging output:**

| customer_id | customer_zip_code | customer_city | customer_state | _loaded_at |
|-------------|-------------------|---------------|----------------|------------|
| c001 | 1310 | São Paulo | SP | 2023-01-01 |
| c002 | 22041 | Rio De Janeiro | RJ | 2023-01-01 |

---

## Naming Conventions

| Convention | Example |
|------------|---------|
| Prefix | `stg__` (double underscore) |
| Source name | `stg__customers`, `stg__orders` |
| Columns | `snake_case` |
| Primary keys | Original source key name |
| Metadata | Prefixed with `_` (e.g., `_loaded_at`) |

---

## Configuration

Staging models are typically configured as:

```yaml
# models/staging/_staging__models.yml
models:
  - name: stg__customers
    config:
      materialized: view  # Views for staging (low storage cost)
      schema: staging
    columns:
      - name: customer_id
        tests:
          - not_null
          - unique
```

---

## Data Flow

```
┌──────────────────────┐         ┌─────────────────────┐
│   SNAPSHOT TABLE     │         │    STAGING MODEL    │
│                      │         │                     │
│  customers_snapshot  │────────▶│   stg__customers    │
│  (SCD2 versioned)    │         │   (cleaned, typed)  │
│                      │         │                     │
└──────────────────────┘         └─────────────────────┘
                                          │
                                          ▼
                                 ┌─────────────────────┐
                                 │  INTERMEDIATE MODEL │
                                 │  or ANALYTICS MODEL │
                                 └─────────────────────┘
```

---

## Best Practices

1. **One staging model per source** — Maintain 1:1 relationship
2. **Use views** — Staging models are typically views (not tables) to save storage
3. **Filter to current records** — Use `WHERE dbt_valid_to IS NULL` for snapshots
4. **No business logic** — Keep transformations purely technical
5. **Test primary keys** — Always test `not_null` and `unique` on PKs

---

*Last updated: December 2025*
