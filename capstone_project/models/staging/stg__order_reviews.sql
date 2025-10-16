{{ config(materialized='view') }}

WITH source AS (
  SELECT * FROM {{ source('sc_raw_data', 'olist_order_reviews') }}
),
renamed AS (
  SELECT
    CAST(review_id AS VARCHAR)                    AS review_id,
    CAST(order_id AS VARCHAR)                     AS order_id,
    CAST(review_score AS NUMBER)                  AS review_score,
    CAST(review_comment_message AS VARCHAR)       AS review_comment_message,
    TRY_TO_TIMESTAMP_NTZ(review_creation_date)    AS review_creation_date,
    TRY_TO_TIMESTAMP_NTZ(review_answer_timestamp) AS review_answer_timestamp,
    CAST(loaded_at AS TIMESTAMP_NTZ)              AS loaded_at,
    CAST(source_system AS VARCHAR)                AS source_system
  FROM source
)
SELECT * FROM renamed
