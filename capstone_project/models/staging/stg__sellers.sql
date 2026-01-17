{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ source('sc_raw_data', 'olist_sellers') }}
),

renamed as (
    select
        'csv' as source_system,
        CAST(seller_id as VARCHAR) as seller_id,
        CAST(seller_zip_code_prefix as VARCHAR) as seller_zip_code_prefix,
        CAST(seller_city as VARCHAR) as seller_city,
        CAST(seller_state as VARCHAR) as seller_state,
        CURRENT_TIMESTAMP() as loaded_at
    from source
)

select * from renamed
