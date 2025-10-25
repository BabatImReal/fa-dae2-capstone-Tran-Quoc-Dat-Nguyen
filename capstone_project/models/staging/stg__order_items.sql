{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ source('sc_raw_data', 'olist_order_items') }}
),

renamed as (
    select
        CAST(order_id as VARCHAR) as order_id,
        CAST(order_item_id as NUMBER) as order_item_id,
        CAST(product_id as VARCHAR) as product_id,
        CAST(seller_id as VARCHAR) as seller_id,
        CAST(shipping_limit_date as TIMESTAMP_NTZ) as shipping_limit_date,
        CAST(price as NUMBER(12, 2)) as price,
        CAST(freight_value as NUMBER(12, 2)) as freight_value,
        CAST(loaded_at as TIMESTAMP_NTZ) as loaded_at,
        CAST(source_system as VARCHAR) as source_system
    from source
)

select * from renamed
