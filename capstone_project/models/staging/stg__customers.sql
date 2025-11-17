{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ ref('customers_snapshot') }}
),

renamed as (
    select
        'snapshot' as source_system,
        dbt_valid_from as effective_from,
        dbt_valid_to as effective_to,
        CAST(customer_id as VARCHAR) as customer_id,
        CAST(customer_unique_id as VARCHAR) as customer_unique_id,
        CAST(customer_zip_code_prefix as VARCHAR) as customer_zip_code_prefix,
        CAST(customer_city as VARCHAR) as customer_city,
        CAST(customer_state as VARCHAR) as customer_state,
        CAST(loaded_at as TIMESTAMP_NTZ) as loaded_at,
        (dbt_valid_to is null) as is_current
    from source
)

select * from renamed
