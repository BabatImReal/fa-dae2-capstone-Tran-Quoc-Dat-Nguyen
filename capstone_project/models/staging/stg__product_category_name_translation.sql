{{ config(materialized='view') }}

with source as (
    select * from {{ source('sc_raw_data', 'product_category_name_translation') }}
),

renamed as (
    select
        CAST(product_category_name as VARCHAR) as product_category_name,
        CAST(product_category_name_english as VARCHAR) as product_category_name_english,
        CAST(loaded_at as TIMESTAMP_NTZ) as loaded_at,
        CAST(source_system as VARCHAR) as source_system
    from source
)

select * from renamed
