{{ config(materialized='ephemeral') }}

with orders as (
    select
        order_id,
        customer_id,
        order_status,
        order_purchase_timestamp,
        order_approved_at,
        order_delivered_carrier_date,
        order_delivered_customer_date,
        order_estimated_delivery_date,
        loaded_at,
        source_system,
        dbt_valid_from,
        dbt_valid_to
    from {{ ref('orders_snapshot') }}
    where dbt_valid_to is null  -- Get only current records
)

select * from orders
