{{ config(materialized='ephemeral') }}

with sellers as (
    select
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state,
        loaded_at,
        source_system,
        dbt_valid_from,
        dbt_valid_to
    from {{ ref('sellers_snapshot') }}
    where dbt_valid_to is null  -- Get only current records
)

select * from sellers
