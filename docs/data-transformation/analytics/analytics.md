# Analytics Layer (Gold)

The **Analytics Layer** contains the final dimensional models optimized for BI tools, dashboards, and ad-hoc analysis. This layer follows the **Kimball dimensional modeling** methodology with **Star Schema** design.

---

## Purpose

- **Dimensional modeling** — Organize data into facts and dimensions
- **Surrogate key generation** — Create stable, warehouse-managed keys
- **Star/snowflake schema** — Optimize for query performance and usability
- **Pre-aggregated metrics** — Provide ready-to-use KPIs
- **BI-friendly** — Designed for end-user consumption

---

## Schema Design: Star Schema

```
                              ┌─────────────────┐
                              │   dim_date      │
                              │   (calendar)    │
                              └────────┬────────┘
                                       │
┌─────────────────┐           ┌────────┴────────┐           ┌─────────────────┐
│  dim_customers  │           │                 │           │  dim_products   │
│                 │◀──────────│   fact_orders   │──────────▶│                 │
└─────────────────┘           │                 │           └─────────────────┘
                              │   (grain: 1     │
┌─────────────────┐           │   order item)   │           ┌─────────────────┐
│  dim_sellers    │◀──────────│                 │──────────▶│ dim_order_      │
│                 │           └────────┬────────┘           │ payment         │
└─────────────────┘                    │                    └─────────────────┘
                                       │
                              ┌────────┴────────┐
                              │ dim_order_      │
                              │ reviews         │
                              └─────────────────┘
```

---

## Dimension Tables

Dimensions provide descriptive context for facts. They answer the "who, what, where, when" questions.

| Dimension | Description | Grain | Key |
|-----------|-------------|-------|-----|
| `dim_customers` | Customer information with geography | 1 row per customer | `customer_key` |
| `dim_products` | Product catalog with categories | 1 row per product | `product_key` |
| `dim_sellers` | Seller information with location | 1 row per seller | `seller_key` |
| `dim_date` | Calendar dimension | 1 row per date | `date_key` |
| `dim_order_payment` | Payment method and details | 1 row per payment | `payment_key` |
| `dim_order_reviews` | Review scores and tiers | 1 row per review | `review_key` |

### Example: dim_customers

```sql
SELECT
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['customer_id']) }} AS customer_key,
    
    -- Natural key
    customer_id,
    
    -- Attributes
    customer_city,
    customer_state,
    customer_zip_code,
    
    -- Derived attributes
    CASE 
        WHEN customer_state IN ('SP', 'RJ', 'MG') THEN 'Southeast'
        WHEN customer_state IN ('RS', 'SC', 'PR') THEN 'South'
        ELSE 'Other'
    END AS customer_region

FROM {{ ref('stg__customers') }}
```

---

## Fact Tables

Facts contain measurable business events and foreign keys to dimensions.

| Fact | Description | Grain | Measures |
|------|-------------|-------|----------|
| `fact_orders` | Order transactions | 1 row per order item | `price`, `freight_value`, `total_value` |

### Example: fact_orders

```sql
SELECT
    -- Surrogate key
    {{ dbt_utils.generate_surrogate_key(['o.order_id', 'oi.order_item_id']) }} AS order_fact_key,
    
    -- Foreign keys to dimensions
    dc.customer_key,
    dp.product_key,
    ds.seller_key,
    dd.date_key AS order_date_key,
    dpy.payment_key,
    dr.review_key,
    
    -- Degenerate dimensions (no separate dim table)
    o.order_id,
    oi.order_item_id,
    
    -- Measures
    oi.price,
    oi.freight_value,
    oi.price + oi.freight_value AS total_value,
    
    -- Timestamps
    o.order_purchase_timestamp,
    o.order_delivered_timestamp,
    
    -- Derived measures
    DATEDIFF('day', o.order_purchase_timestamp, o.order_delivered_timestamp) AS delivery_days

FROM {{ ref('stg__orders') }} o
JOIN {{ ref('int__order_items') }} oi ON o.order_id = oi.order_id
JOIN {{ ref('dim_customers') }} dc ON o.customer_id = dc.customer_id
JOIN {{ ref('dim_products') }} dp ON oi.product_id = dp.product_id
JOIN {{ ref('dim_sellers') }} ds ON oi.seller_id = ds.seller_id
JOIN {{ ref('dim_date') }} dd ON o.order_purchase_timestamp::DATE = dd.date_value
LEFT JOIN {{ ref('dim_order_payment') }} dpy ON o.order_id = dpy.order_id
LEFT JOIN {{ ref('dim_order_reviews') }} dr ON o.order_id = dr.order_id
```

---

## Surrogate Keys

Surrogate keys are warehouse-generated identifiers that:
- Remain stable even if natural keys change
- Enable SCD Type 2 tracking
- Improve join performance

**Generation using dbt_utils:**

```sql
{{ dbt_utils.generate_surrogate_key(['customer_id']) }} AS customer_key
```

---

## Configuration

Analytics models are materialized as **tables** or **incremental** for performance:

```yaml
# models/marts/_marts__models.yml
models:
  - name: fact_orders
    config:
      materialized: incremental
      unique_key: order_fact_key
      schema: analytics
    description: Order fact table at order item grain
    
  - name: dim_customers
    config:
      materialized: table
      schema: analytics
    description: Customer dimension with geography
```

---

## Naming Conventions

| Type | Prefix | Example |
|------|--------|---------|
| Dimension | `dim_` | `dim_customers`, `dim_products` |
| Fact | `fact_` | `fact_orders`, `fact_payments` |
| Bridge (many-to-many) | `bridge_` | `bridge_order_products` |
| Aggregate | `agg_` | `agg_daily_sales` |

---

## Star Schema vs Snowflake Schema

| Aspect | Star Schema | Snowflake Schema |
|--------|-------------|------------------|
| **Design** | Denormalized dimensions | Normalized dimensions |
| **Joins** | Fewer joins | More joins |
| **Performance** | Faster queries | Slower queries |
| **Storage** | More redundancy | Less redundancy |
| **Maintenance** | Simpler | More complex |

**This project uses Star Schema** for simplicity and query performance.

---

## Data Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    STAGING      │    │  INTERMEDIATE   │    │   ANALYTICS     │
│                 │    │                 │    │                 │
│  stg__customers │───▶│                 │───▶│  dim_customers  │
│  stg__products  │───▶│  int__products  │───▶│  dim_products   │
│  stg__sellers   │───▶│                 │───▶│  dim_sellers    │
│  stg__orders    │───▶│  int__order_    │───▶│  fact_orders    │
│  stg__order_    │───▶│  items          │    │                 │
│  items          │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                      │
                                                      ▼
                                              ┌─────────────────┐
                                              │   BI TOOLS      │
                                              │   (Metabase)    │
                                              └─────────────────┘
```

---

## Best Practices

1. **Use surrogate keys** — Don't expose natural keys to BI tools
2. **Materialize as tables** — Analytics models need fast query performance
3. **Incremental where possible** — Use incremental materialization for large fact tables
4. **Pre-calculate metrics** — Add commonly used calculations to facts
5. **Document thoroughly** — Add descriptions for all columns
6. **Test referential integrity** — Ensure all FK relationships are valid

---

*Last updated: December 2025*
