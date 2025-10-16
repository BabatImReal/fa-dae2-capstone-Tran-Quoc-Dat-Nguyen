{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('sc_raw_data', 'olist_order_items')}}
),
renamed AS (
    SELECT  
        CAST(order_id AS VARCHAR)                         AS order_id,
        CAST(order_item_id AS NUMBER)                    AS order_item_id,
        CAST(product_id AS VARCHAR)                       AS product_id,
        CAST(seller_id AS VARCHAR)                        AS seller_id,
        CAST(shipping_limit_date AS TIMESTAMP_NTZ)        AS shipping_limit_date,
        CAST(price AS NUMBER(12,2))                       AS price,
        CAST(freight_value AS NUMBER(12,2))               AS freight_value,
        CAST(loaded_at AS TIMESTAMP_NTZ)                  AS loaded_at,
        CAST(source_system AS VARCHAR)                    AS source_system
    FROM source
)
SELECT * FROM renamed