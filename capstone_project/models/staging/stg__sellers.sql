{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ ref('sellers_snapshot') }}
),

renamed as (
    select
        'snapshot' as source_system,
        dbt_valid_from as effective_from,
        dbt_valid_to as effective_to,
        CAST(seller_id as VARCHAR) as seller_id,
        CAST(seller_zip_code_prefix as VARCHAR) as seller_zip_code_prefix,
        CAST(seller_city as VARCHAR) as seller_city,
        CAST(seller_state as VARCHAR) as seller_state,
        CAST(loaded_at as TIMESTAMP_NTZ) as loaded_at,
        (dbt_valid_to is null) as is_current
    from source
)

select * from renamed
