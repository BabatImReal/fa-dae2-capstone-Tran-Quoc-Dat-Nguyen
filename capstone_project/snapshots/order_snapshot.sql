{% snapshot orders_snapshot %}
{{
  config(
    target_schema='snapshots',
    unique_key='order_id',
    strategy='check',
    check_cols=[
      'customer_id',
      'order_status',
      'order_purchase_timestamp',
      'order_approved_at',
      'order_delivered_carrier_date',
      'order_delivered_customer_date',
      'order_estimated_delivery_date'
    ],
    invalidate_hard_deletes=true
  )
}}
    select
        order_id,
        customer_id,
        order_status,
        order_purchase_timestamp,
        order_approved_at,
        order_delivered_carrier_date,
        order_delivered_customer_date,
        order_estimated_delivery_date,
        loaded_at
    from {{ source('sc_raw_data', 'olist_orders') }}
{% endsnapshot %}
