{{ config(materialized='view') }}

WITH source AS (
  SELECT * FROM {{ source('sc_raw_data', 'product_category_name_translation') }}
),
renamed AS (
  SELECT
    CAST(product_category_name AS VARCHAR)          AS product_category_name,
    CAST(product_category_name_english AS VARCHAR)  AS product_category_name_english,
    CAST(loaded_at AS TIMESTAMP_NTZ)                AS loaded_at,
    CAST(source_system AS VARCHAR)                  AS source_system
  FROM source
)
SELECT * FROM renamed
