{{ config(materialized='view') }}

with orders as (
    select
        order_id,
        order_status,
        customer_id,
        order_purchase_timestamp,
        order_delivered_customer_date,
        order_estimated_delivery_date
    from {{ ref('stg__orders') }}
),

items as (
    select
        order_id,
        order_item_id,
        product_id,              -- FIX: add comma
        seller_id,
        price,
        freight_value,
        shipping_limit_date
    from {{ ref('stg__order_items') }}
),

joined as (
    select
        o.order_id,
        o.order_status,                 -- keep order grain
        max(o.customer_id) as customer_id,                     -- representative seller per order
        min(i.seller_id) as seller_id,                   -- representative product per order
        min(i.product_id) as product_id,
        max(datediff('day', o.order_purchase_timestamp, o.order_delivered_customer_date)) as shipping_date,
        max(i.shipping_limit_date) as shipping_limit_date,
        count(i.order_item_id) as order_qty,
        (avg(i.price + i.freight_value) * count(i.order_item_id)) as total_order_value,
        case
            when max(o.order_estimated_delivery_date) is null or max(o.order_delivered_customer_date) is null then null
            when max(o.order_estimated_delivery_date) < max(o.order_delivered_customer_date) then 1
            else 0
        end as order_check_flag
    from orders as o
    inner join items as i on o.order_id = i.order_id
    group by o.order_id, o.order_status
)

select
    order_id,
    customer_id,
    seller_id,
    product_id,                                         -- NEW: exposed
    order_status,
    shipping_date,
    shipping_limit_date,
    order_qty,
    total_order_value,
    order_check_flag
from joined
