{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ ref('products_snapshot') }}
),

renamed as (
    select
        'snapshot' as source_system,
        dbt_valid_from as effective_from,
        dbt_valid_to as effective_to,
        CAST(product_id as VARCHAR) as product_id,
        CAST(product_category_name as VARCHAR) as product_category_name,
        CAST(product_name_length as NUMBER) as product_name_length,
        CAST(product_description_length as NUMBER) as product_description_length,
        CAST(product_photos_qty as NUMBER) as product_photos_qty,
        CAST(product_weight_g as NUMBER(12, 4)) as product_weight_g,
        CAST(product_length_cm as NUMBER(12, 4)) as product_length_cm,
        CAST(product_height_cm as NUMBER(12, 4)) as product_height_cm,
        CAST(product_width_cm as NUMBER(12, 4)) as product_width_cm,
        CAST(loaded_at as TIMESTAMP_LTZ) as loaded_at,
        (dbt_valid_to is null) as is_current
    from source
)

select * from renamed
