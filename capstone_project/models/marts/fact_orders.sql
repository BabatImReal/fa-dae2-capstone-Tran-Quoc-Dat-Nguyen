{{ config(
    materialized = 'incremental',
    unique_key=['order_id', 'product_id', 'seller_id'],
    schema='sc_analytics',
    cluster_by=['order_purchase_timestamp::date'],
    incremental_strategy='merge',
    on_schema_change='sync_all_columns',
    post_hook=[
      "delete from {{ this }} where order_id not in (select order_id from {{ ref('stg__orders') }})"
    ]
) }}

with orders as (
    select o.*
    from {{ ref('stg__orders') }} as o
),

dim_customers as (
    select
        customer_id,
        customer_key,
        effective_from,
        effective_to
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
        order_payment_key,
        primary_payment_type
    from {{ ref('dim_order_payment') }}
),

dim_order_reviews as (
    select
        order_id,
        order_review_key,
        review_score,
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
        product_id,
        seller_id,
        order_status,
        shipping_date,
        shipping_limit_date,
        order_qty,
        total_order_value,
        order_check_flag
    from {{ ref('int__order_items') }}
),

dim_product as (
    select
        product_id,
        product_key,
        product_category_name_english
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
    -- natural/surrogate key
    {{ dbt_utils.generate_surrogate_key(['o.order_id', 'ioi.product_id', 'ioi.seller_id']) }} as order_key,
    o.order_id,

    -- dimension surrogate keys
    c.customer_key,              -- FIXED: Now properly joined
    s.seller_key,
    p.order_payment_key,
    r.order_review_key,
    dp.product_key,              -- FIXED: Now properly joined

    -- natural ids (for traceability)
    o.customer_id,
    ioi.product_id,              -- FIXED: Added from int_order_items
    ioi.seller_id,
    
    -- dimension attributes (for easier querying)
    dp.product_category_name_english,  -- FIXED: Now properly joined

    -- order attributes
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,

    -- measures
    p.primary_payment_type,
    ioi.order_qty,
    ioi.total_order_value,
    ioi.shipping_date,
    {{ calculate_shipping_performance_tier('ioi.shipping_date') }} as shipping_tier,
    ioi.shipping_limit_date,
    ioi.order_check_flag,
    r.review_score,
    {{ calculate_review_score_tier('r.review_score') }} as review_tier,

    -- metadata
    o.loaded_at,
    current_timestamp() as dbt_updated_at

from orders as o
inner join int_order_items as ioi           -- CHANGED: inner join (orders must have items)
    on o.order_id = ioi.order_id

left join dim_customers as c
    on o.customer_id = c.customer_id
    and c.effective_to is null              -- Current customer record only

left join dim_sellers as s
    on ioi.seller_id = s.seller_id

left join dim_order_payment as p
    on o.order_id = p.order_id

left join first_review_record as r
    on o.order_id = r.order_id

left join dim_product as dp                  -- FIXED: Join on correct source
    on ioi.product_id = dp.product_id

{% if is_incremental() %}
where
    o.loaded_at > (
        select dateadd(day, -1, coalesce(max(loaded_at), '1900-01-01'::timestamp_ntz))
        from {{ this }}
    )
{% endif %}
