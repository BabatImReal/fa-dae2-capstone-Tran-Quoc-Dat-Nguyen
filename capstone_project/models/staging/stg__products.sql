{{ config(materialized='view') }}

WITH source AS (
  SELECT * FROM {{ source('sc_raw_data', 'olist_products') }}
),
renamed AS (
  SELECT
    CAST(product_id AS VARCHAR)                         AS product_id,
    CAST(product_category_name AS VARCHAR)              AS product_category_name,
    CAST(product_name_length AS NUMBER)                 AS product_name_length,
    CAST(product_description_length AS NUMBER)          AS product_description_length,
    CAST(product_photos_qty AS NUMBER)                  AS product_photos_qty,
    CAST(product_weight_g AS NUMBER(12,4))              AS product_weight_g,
    CAST(product_length_cm AS NUMBER(12,4))             AS product_length_cm,
    CAST(product_height_cm AS NUMBER(12,4))             AS product_height_cm,
    CAST(product_width_cm AS NUMBER(12,4))              AS product_width_cm,
    CAST(loaded_at AS TIMESTAMP_NTZ)                    AS loaded_at,
    CAST(source_system AS VARCHAR)                      AS source_system
  FROM source
)
SELECT * FROM renamed
