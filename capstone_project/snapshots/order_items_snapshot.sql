{% snapshot order_items_snapshot %}
{{
  config(
    target_schema='snapshots',
    unique_key=['order_id', 'order_item_id'],
    strategy='check',
    check_cols=[
      'product_id',
      'seller_id',
      'shipping_limit_date',
      'price',
      'freight_value'
    ],
    invalidate_hard_deletes=true
  )
}}
select
    order_id,
    order_item_id,
    product_id,
    seller_id,
    shipping_limit_date,
    price,
    freight_value,
    loaded_at
from {{ source('sc_raw_data', 'olist_order_items') }}
{% endsnapshot %}
