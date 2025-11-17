{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ ref('order_payments_snapshot') }}
),

renamed as (
    select
        'snapshot' as source_system,
        dbt_valid_from as effective_from,
        dbt_valid_to as effective_to,
        CAST(order_id as VARCHAR) as order_id,
        CAST(payment_sequential as NUMBER) as payment_sequential,
        CAST(payment_type as VARCHAR) as payment_type,
        CAST(payment_installments as NUMBER) as payment_installments,
        CAST(payment_value as NUMBER(12, 2)) as payment_value,
        CAST(loaded_at as TIMESTAMP_NTZ) as loaded_at,
        (dbt_valid_to is null) as is_current
    from source
)

select * from renamed
