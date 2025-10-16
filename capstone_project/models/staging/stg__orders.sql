{{ config(materialized='view') }}

WITH source AS (
  SELECT * FROM {{ source('sc_raw_data', 'olist_orders') }}
),
renamed AS (
  SELECT
    CAST(order_id AS VARCHAR)                           AS order_id,
    CAST(customer_id AS VARCHAR)                        AS customer_id,
    CAST(order_status AS VARCHAR)                       AS order_status,
    CAST(order_purchase_timestamp AS TIMESTAMP_NTZ)     AS order_purchase_timestamp,
    CAST(order_approved_at AS TIMESTAMP_NTZ)            AS order_approved_at,
    CAST(order_delivered_carrier_date AS TIMESTAMP_NTZ) AS order_delivered_carrier_date,
    CAST(order_delivered_customer_date AS TIMESTAMP_NTZ)AS order_delivered_customer_date,
    CAST(order_estimated_delivery_date AS TIMESTAMP_NTZ)AS order_estimated_delivery_date,
    CAST(loaded_at AS TIMESTAMP_NTZ)                    AS loaded_at,
    CAST(source_system AS VARCHAR)                      AS source_system
  FROM source
)
SELECT * FROM renamed