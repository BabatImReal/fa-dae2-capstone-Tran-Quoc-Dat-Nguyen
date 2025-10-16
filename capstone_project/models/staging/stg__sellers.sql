{{ config(materialized='view') }}

WITH source AS (
  SELECT * FROM {{ source('sc_raw_data', 'olist_sellers') }}
),
renamed AS (
  SELECT
    CAST(seller_id AS VARCHAR)                  AS seller_id,
    CAST(seller_zip_code_prefix AS VARCHAR)     AS seller_zip_code_prefix,
    CAST(seller_city AS VARCHAR)                AS seller_city,
    CAST(seller_state AS VARCHAR)               AS seller_state,
    CAST(loaded_at AS TIMESTAMP_NTZ)            AS loaded_at,
    CAST(source_system AS VARCHAR)              AS source_system
  FROM source
)
SELECT * FROM renamed
