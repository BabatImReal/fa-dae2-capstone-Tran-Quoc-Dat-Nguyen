{{ config(materialized='view') }}

WITH source AS (
  SELECT * FROM {{ source('sc_raw_data', 'olist_geolocation') }}
),
renamed AS (
  SELECT
    CAST(geolocation_zip_code_prefix AS VARCHAR) AS geolocation_zip_code_prefix,
    CAST(geolocation_lat AS NUMBER(12,8))        AS geolocation_lat,
    CAST(geolocation_lng AS NUMBER(12,8))        AS geolocation_lng,
    CAST(geolocation_city AS VARCHAR)            AS geolocation_city,
    CAST(geolocation_state AS VARCHAR)           AS geolocation_state,
    CAST(loaded_at AS TIMESTAMP_NTZ)             AS loaded_at,
    CAST(source_system AS VARCHAR)               AS source_system
  FROM source
)
SELECT * FROM renamed
