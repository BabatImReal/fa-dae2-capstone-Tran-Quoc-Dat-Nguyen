{{ config(materialized='table') }}

WITH date_spine AS (
    select
      dateadd('day', seq4(), '2020-01-01'::date) as date_value
    from table(generator(rowcount => 36525)) -- ~100 years; adjust as needed
),
date_attributes AS (
    SELECT
        date_value,
        -- Date components
        YEAR(date_value) as year,
        MONTH(date_value) as month,
        DAY(date_value) as day,
        DAYOFWEEK(date_value) as day_of_week,
        DAYOFYEAR(date_value) as day_of_year,
        -- Fiscal periods
        QUARTER(date_value) as quarter,
        CASE
            WHEN MONTH(date_value) IN (1, 2, 3) THEN 'Q1'
            WHEN MONTH(date_value) IN (4, 5, 6) THEN 'Q2'
            WHEN MONTH(date_value) IN (7, 8, 9) THEN 'Q3'
            ELSE 'Q4'
        END as fiscal_quarter,
        -- Business logic
        CASE
            WHEN dayofweekiso(date_value) IN (6, 7) THEN TRUE
            ELSE FALSE
        END as is_weekend,
        CASE
            WHEN date_value = CURRENT_DATE() THEN TRUE
            ELSE FALSE
        END as is_today
    FROM date_spine
    WHERE date_value <= CURRENT_DATE()
)
SELECT
    date_value as date_id,
    *
    -- CURRENT_TIMESTAMP() as dbt_updated_at  -- keep as-is if already present
FROM date_attributes