# Intermediate Layer (Silver)

The **Intermediate Layer** applies business transformations to create derived attributes and prepare data for the analytics layer. This is where business logic lives.

---

## Purpose

- **Business logic implementation** — Apply domain-specific rules and calculations
- **Derived columns** — Create calculated fields based on business requirements
- **Joins between staging tables** — Combine related entities
- **Data enrichment** — Add context from reference tables
- **Aggregations** — Pre-aggregate data where useful

---

## What Intermediate Does NOT Do

❌ Not exposed directly to end users or BI tools  
❌ Not the final dimensional model  
❌ No surrogate key generation (that's in analytics)  

Intermediate models are **internal building blocks** for the analytics layer.

---

## Intermediate Models

| Model | Description | Joins |
|-------|-------------|-------|
| `int__products` | Products enriched with translated category names | `stg__products` + `stg__product_category_name_translation` |
| `int__order_items` | Order items with product and seller context | `stg__order_items` + `stg__products` + `stg__sellers` |

---

## Example: Intermediate Products

**Purpose:** Enrich products with English category names (original data has Portuguese).

**Staging inputs:**

`stg__products`:
| product_id | product_category_name | product_weight_g |
|------------|----------------------|------------------|
| p001 | beleza_saude | 500 |
| p002 | informatica_acessorios | 200 |

`stg__product_category_name_translation`:
| product_category_name | product_category_name_english |
|----------------------|------------------------------|
| beleza_saude | health_beauty |
| informatica_acessorios | computers_accessories |

**Intermediate model** (`models/intermediate/int__products.sql`):

```sql
WITH products AS (
    SELECT * FROM {{ ref('stg__products') }}
),

translations AS (
    SELECT * FROM {{ ref('stg__product_category_name_translation') }}
),

enriched AS (
    SELECT
        p.product_id,
        p.product_category_name AS product_category_name_pt,
        COALESCE(t.product_category_name_english, 'unknown') AS product_category_name,
        p.product_weight_g,
        
        -- Derived: weight in kg
        ROUND(p.product_weight_g / 1000.0, 2) AS product_weight_kg,
        
        -- Derived: size category
        CASE
            WHEN p.product_weight_g < 500 THEN 'small'
            WHEN p.product_weight_g < 2000 THEN 'medium'
            ELSE 'large'
        END AS product_size_category
        
    FROM products p
    LEFT JOIN translations t
        ON p.product_category_name = t.product_category_name
)

SELECT * FROM enriched
```

**Intermediate output:**

| product_id | product_category_name | product_weight_kg | product_size_category |
|------------|----------------------|-------------------|----------------------|
| p001 | health_beauty | 0.50 | small |
| p002 | computers_accessories | 0.20 | small |

---

## Example: Intermediate Order Items

**Purpose:** Combine order items with product and seller information.

```sql
WITH order_items AS (
    SELECT * FROM {{ ref('stg__order_items') }}
),

products AS (
    SELECT * FROM {{ ref('int__products') }}
),

sellers AS (
    SELECT * FROM {{ ref('stg__sellers') }}
),

enriched AS (
    SELECT
        oi.order_id,
        oi.order_item_id,
        oi.product_id,
        oi.seller_id,
        oi.price,
        oi.freight_value,
        
        -- From products
        p.product_category_name,
        p.product_size_category,
        
        -- From sellers
        s.seller_city,
        s.seller_state,
        
        -- Derived: total item value
        oi.price + oi.freight_value AS total_item_value
        
    FROM order_items oi
    LEFT JOIN products p ON oi.product_id = p.product_id
    LEFT JOIN sellers s ON oi.seller_id = s.seller_id
)

SELECT * FROM enriched
```

---

## Naming Conventions

| Convention | Example |
|------------|---------|
| Prefix | `int__` (double underscore) |
| Descriptive name | `int__products`, `int__order_items` |
| Derived columns | Descriptive names (e.g., `product_size_category`) |

---

## Configuration

Intermediate models are typically configured as:

```yaml
# models/intermediate/_intermediate__models.yml
models:
  - name: int__products
    config:
      materialized: view  # or ephemeral for truly internal models
      schema: intermediate
    description: Products enriched with translated category names
```

---

## Data Flow

```
┌─────────────────┐     ┌─────────────────┐
│  stg__products  │     │  stg__product_  │
│                 │     │  category_...   │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
           ┌─────────────────┐
           │  int__products  │
           │  (enriched)     │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │  dim_products   │
           │  (analytics)    │
           └─────────────────┘
```

---

## Best Practices

1. **Use for complex joins** — When staging tables need to be combined
2. **Apply business logic here** — Calculations, categorizations, flags
3. **Keep internal** — Not for direct BI consumption
4. **Use views or ephemeral** — Minimize storage for intermediate results
5. **Document derived columns** — Explain business logic in comments

---

*Last updated: December 2025*
