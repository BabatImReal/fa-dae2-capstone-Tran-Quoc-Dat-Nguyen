{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ source('sc_raw_data', 'olist_order_reviews') }}
),

renamed as (
    select
        CAST(review_id as VARCHAR) as review_id,
        CAST(order_id as VARCHAR) as order_id,
        CAST(review_score as NUMBER) as review_score,
        CAST(review_comment_message as VARCHAR) as review_comment_message,
        TRY_TO_TIMESTAMP_NTZ(review_creation_date) as review_creation_date,
        TRY_TO_TIMESTAMP_NTZ(review_answer_timestamp) as review_answer_timestamp,
        CAST(loaded_at as TIMESTAMP_NTZ) as loaded_at,
        CAST(source_system as VARCHAR) as source_system
    from source
)

select * from renamed
