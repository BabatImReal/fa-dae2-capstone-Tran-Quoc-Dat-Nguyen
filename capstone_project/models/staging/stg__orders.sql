{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ ref('orders_snapshot') }}
),

renamed as (
    select
        CAST(order_id as VARCHAR) as order_id,
        CAST(customer_id as VARCHAR) as customer_id,
        CAST(order_status as VARCHAR) as order_status,
        CAST(order_purchase_timestamp as TIMESTAMP_NTZ) as order_purchase_timestamp,
        CAST(order_approved_at as TIMESTAMP_NTZ) as order_approved_at,
        CAST(order_delivered_carrier_date as TIMESTAMP_NTZ) as order_delivered_carrier_date,
        CAST(order_delivered_customer_date as TIMESTAMP_NTZ) as order_delivered_customer_date,
        CAST(order_estimated_delivery_date as TIMESTAMP_NTZ) as order_estimated_delivery_date,
        CURRENT_TIMESTAMP() as loaded_at,
        'csv' as source_system
    from source
)

select * from renamed
