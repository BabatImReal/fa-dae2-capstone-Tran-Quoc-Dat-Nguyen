{{ config(
    materialized = 'incremental',
    unique_key='order_id'
) }}

with orders as (
  select
    o.*
  from {{ ref('stg__orders') }} o
  {% if is_incremental() %}
  where o.loaded_at > (
    select coalesce(max(loaded_at), cast('1900-01-01' as timestamp_ntz)) from {{ this }}
  )
  {% endif %}
),
dim_customers as (
  select customer_id, customer_key
  from {{ ref('dim_customers') }}
),
dim_sellers as (
  select seller_id, seller_key
  from {{ ref('dim_sellers') }}
),
dim_order_payment as (
  select order_id, order_payment_key
  from {{ ref('dim_order_payment') }}
),
dim_order_reviews as (
  select
    order_id,
    order_review_key,
    review_score,                                -- ADDED
    review_answer_timestamp,
    review_creation_date,
    row_number() over (
      partition by order_id
      order by review_answer_timestamp desc nulls last, review_creation_date desc nulls last
    ) as rn
  from {{ ref('dim_order_reviews') }}
),
int_order_items as (
  select
    order_id,
    customer_id,
    seller_id,
    order_status,
    shipping_date,
    shipping_limit_date,
    shipping_sla_days,
    order_qty,
    total_order_value,
    delivered_after_sla_days,
    order_check_flag
  from {{ ref('int__order_items') }}
)

select
  -- natural key
  o.order_id,

  -- dimension surrogate keys
  c.customer_key,
  s.seller_key,
  p.order_payment_key,
  r.order_review_key,                     

  -- natural ids (traceability)
  o.customer_id,
  ioi.seller_id,

  -- order attributes
  o.order_status,
  o.order_purchase_timestamp,
  o.order_approved_at,
  o.order_delivered_carrier_date,
  o.order_delivered_customer_date,
  o.order_estimated_delivery_date,

  -- measures
  ioi.order_qty,
  ioi.total_order_value,
  ioi.shipping_date,
  ioi.shipping_limit_date,
  ioi.shipping_sla_days,
  ioi.delivered_after_sla_days,
  ioi.order_check_flag,
  r.review_score as review_score, 

  -- metadata
  o.loaded_at,
  current_timestamp() as dbt_updated_at
from orders o
left join int_order_items ioi
  on o.order_id = ioi.order_id
left join dim_customers c
  on o.customer_id = c.customer_id
left join dim_sellers s
  on ioi.seller_id = s.seller_id
left join dim_order_payment p
  on o.order_id = p.order_id
left join (
  select order_id, order_review_key, review_score 
  from dim_order_reviews
  where rn = 1
) r
  on o.order_id = r.order_id
