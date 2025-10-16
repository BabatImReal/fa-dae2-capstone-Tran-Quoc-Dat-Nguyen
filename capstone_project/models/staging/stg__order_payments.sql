{{ config(materialized='view') }}

WITH source AS (
  SELECT * FROM {{ source('sc_raw_data', 'olist_order_payments') }}
),
renamed AS (
  SELECT 
    CAST(order_id AS VARCHAR)               AS order_id,
    CAST(payment_sequential AS NUMBER)      AS payment_sequential,
    CAST(payment_type AS VARCHAR)           AS payment_type,
    CAST(payment_installments AS NUMBER)    AS payment_installments,
    CAST(payment_value AS NUMBER(12,2))     AS payment_value,
    CAST(loaded_at AS TIMESTAMP_NTZ)        AS loaded_at,
    CAST(source_system AS VARCHAR)          AS source_system
  FROM source
)
SELECT * FROM renamed