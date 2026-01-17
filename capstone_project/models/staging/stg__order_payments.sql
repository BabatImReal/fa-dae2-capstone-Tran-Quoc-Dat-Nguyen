{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ source('sc_raw_data', 'olist_order_payments') }}
),

renamed as (
    select
        'csv' as source_system,
        CAST(order_id as VARCHAR) as order_id,
        CAST(payment_sequential as NUMBER) as payment_sequential,
        CAST(payment_type as VARCHAR) as payment_type,
        CAST(payment_installments as NUMBER) as payment_installments,
        CAST(payment_value as NUMBER(12, 2)) as payment_value,
        CURRENT_TIMESTAMP() as loaded_at
    from source
)

select * from renamed
