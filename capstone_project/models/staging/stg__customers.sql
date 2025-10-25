{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ source('sc_raw_data', 'olist_customers') }}
),

renamed as (
    select
        CAST(customer_id as VARCHAR) as customer_id,
        CAST(customer_unique_id as VARCHAR) as customer_unique_id,
        CAST(customer_zip_code_prefix as VARCHAR) as customer_zip_code_prefix,
        CAST(customer_city as VARCHAR) as customer_city,
        CAST(customer_state as VARCHAR) as customer_state,
        CAST(loaded_at as TIMESTAMP_NTZ) as loaded_at,
        CAST(source_system as VARCHAR) as source_system
    from source
)

select * from renamed
