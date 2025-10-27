{{ config(
    materialized = 'incremental',
    unique_key='order_key',
    schema='sc_analytics',
    incremental_strategy='merge'
) }}

with orders as (
    select o.*
    from {{ ref('stg__orders') }} as o
),

dim_customers as (
    select
        customer_id,
        customer_key,
        effective_from,   -- added
        effective_to      -- added
    from {{ ref('dim_customers') }}
),

dim_sellers as (
    select
        seller_id,
        seller_key
    from {{ ref('dim_sellers') }}
),

dim_order_payment as (
    select
        order_id,
        order_payment_key
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
        product_id,
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
),

dim_product as (
    select
        product_id,
        product_key,                  -- ADDED
        product_category_english
    from {{ ref('dim_products') }}
),

first_review_record as (
    select
        order_id,
        order_review_key,
        review_score
    from dim_order_reviews
    where rn = 1
)

select
    -- natural key
    {{ dbt_utils.generate_surrogate_key(['o.order_id', 'o.loaded_at']) }} as order_key,
    o.order_id,

    -- dimension surrogate keys
    c.customer_key,
    s.seller_key,
    p.order_payment_key,
    r.order_review_key,
    dp.product_key,
    dp.product_id,        -- ADDED
    dp.product_category_english,               -- ADDED

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
    r.review_score,

    -- metadata
    o.loaded_at,
    current_timestamp() as dbt_updated_at   -- ensure compiled tmp has this column for MERGE

from orders as o
left join int_order_items as ioi
    on o.order_id = ioi.order_id

left join dim_customers as c
    on
        o.customer_id = c.customer_id
        and c.effective_to is null  -- Always use current customer

left join dim_sellers as s
    on ioi.seller_id = s.seller_id
left join dim_order_payment as p
    on o.order_id = p.order_id
left join first_review_record as r
    on o.order_id = r.order_id
left join dim_product as dp
    on ioi.product_id = dp.product_id

{% if is_incremental() %}
    where
        o.order_purchase_timestamp > (
            select coalesce(max(order_purchase_timestamp), '1900-01-01'::timestamp_ntz)
            from {{ this }}
        )
{% endif %}
