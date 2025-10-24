{{ config(materialized='view') }}

with source as (
    select * from {{ source('sc_raw_data', 'olist_order_payments') }}
),

renamed as (
    select
        CAST(order_id as VARCHAR) as order_id,
        CAST(payment_sequential as NUMBER) as payment_sequential,
        CAST(payment_type as VARCHAR) as payment_type,
        CAST(payment_installments as NUMBER) as payment_installments,
        CAST(payment_value as NUMBER(12, 2)) as payment_value,
        CAST(loaded_at as TIMESTAMP_NTZ) as loaded_at,
        CAST(source_system as VARCHAR) as source_system
    from source
)

select * from renamed
