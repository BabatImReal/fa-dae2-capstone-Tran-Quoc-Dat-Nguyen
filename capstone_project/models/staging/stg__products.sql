{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ source('sc_raw_data', 'olist_products') }}
),

renamed as (
    select
        'csv' as source_system,
        CAST(product_id as VARCHAR) as product_id,
        CAST(product_category_name as VARCHAR) as product_category_name,
        CAST(product_name_length as NUMBER) as product_name_length,
        CAST(product_description_length as NUMBER) as product_description_length,
        CAST(product_photos_qty as NUMBER) as product_photos_qty,
        CAST(product_weight_g as NUMBER(12, 4)) as product_weight_g,
        CAST(product_length_cm as NUMBER(12, 4)) as product_length_cm,
        CAST(product_height_cm as NUMBER(12, 4)) as product_height_cm,
        CAST(product_width_cm as NUMBER(12, 4)) as product_width_cm,
        CURRENT_TIMESTAMP() as loaded_at
    from source
)

select * from renamed
