{{ config(materialized='view') }}

with orders as (
    select
        order_id,
        order_status,
        customer_id,
        order_purchase_timestamp,
        order_delivered_customer_date,
        order_estimated_delivery_date
    from {{ ref('int__orders') }}
),

items as (
    select
        order_id,
        order_item_id,
        product_id,
        seller_id,
        price,
        freight_value,
        shipping_limit_date
    from {{ ref('order_items_snapshot') }}
    where dbt_valid_to is null  -- Filter for latest records
),

joined as (
    select
        o.order_id,
        o.order_status,                 -- keep order grain
        cast(max(i.shipping_limit_date) as timestamp_ntz) as shipping_limit_date,                     -- representative seller per order
        cast((avg(i.price + i.freight_value) * count(i.order_item_id)) as number(38, 8)) as total_order_value,                   -- representative product per order
        max(o.customer_id) as customer_id,
        min(i.seller_id) as seller_id,
        min(i.product_id) as product_id,
        max(datediff('day', o.order_purchase_timestamp, o.order_delivered_customer_date)) as shipping_date,
        count(i.order_item_id) as order_qty,
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
qualify row_number() over (partition by order_id, product_id, seller_id order by order_qty desc) = 1
