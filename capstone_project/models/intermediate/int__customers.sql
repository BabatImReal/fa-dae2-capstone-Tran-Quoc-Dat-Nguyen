{{ config(materialized='ephemeral') }}

with customers as (
    select
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state,
        loaded_at,
        source_system,
        dbt_valid_from,
        dbt_valid_to
    from {{ ref('customers_snapshot') }}
    where dbt_valid_to is null  -- Get only current records
)

select * from customers
