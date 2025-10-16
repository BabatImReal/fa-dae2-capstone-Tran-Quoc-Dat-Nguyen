{{ config(materialized='view') }}

WITH source AS (
  SELECT * FROM {{ source('sc_raw_data', 'olist_customers') }}
),
renamed AS (
  SELECT
    CAST(customer_id AS VARCHAR)              AS customer_id,
    CAST(customer_unique_id AS VARCHAR)       AS customer_unique_id,
    CAST(customer_zip_code_prefix AS VARCHAR) AS customer_zip_code_prefix,
    CAST(customer_city AS VARCHAR)            AS customer_city,
    CAST(customer_state AS VARCHAR)           AS customer_state,
    CAST(loaded_at AS TIMESTAMP_NTZ)          AS loaded_at,
    CAST(source_system AS VARCHAR)            AS source_system
  FROM source
)
SELECT * FROM renamed
