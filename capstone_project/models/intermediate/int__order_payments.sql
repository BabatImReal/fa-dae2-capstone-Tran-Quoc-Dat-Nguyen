{{ config(materialized='ephemeral') }}

with order_payments as (
    select
        order_id,
        payment_sequential,
        payment_type,
        payment_installments,
        payment_value,
        loaded_at,
        source_system,
        dbt_valid_from,
        dbt_valid_to
    from {{ ref('order_payments_snapshot') }}
    where dbt_valid_to is null  -- Get only current records
)

select * from order_payments
