{% snapshot order_payments_snapshot %}
{{
  config(
    target_schema='snapshots',
    unique_key=['order_id', 'payment_sequential'],
    strategy='check',
    check_cols=['payment_type', 'payment_installments', 'payment_value'],
    invalidate_hard_deletes=true
  )
}}
    select
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value,
        loaded_at,
        source_system
    from {{ ref('stg__order_payments') }}
{% endsnapshot %}
