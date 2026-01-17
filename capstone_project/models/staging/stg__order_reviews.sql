{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ source('sc_raw_data', 'olist_order_reviews') }}
),

renamed as (
    select
        'csv' as source_system,
        CAST(review_id as VARCHAR) as review_id,
        CAST(order_id as VARCHAR) as order_id,
        CAST(review_score as NUMBER) as review_score,
        CAST(review_comment_title as VARCHAR) as review_comment_title,
        CAST(review_comment_message as VARCHAR) as review_comment_message,
        TRY_TO_TIMESTAMP_NTZ(review_creation_date) as review_creation_date,
        TRY_TO_TIMESTAMP_NTZ(review_answer_timestamp) as review_answer_timestamp,
        CURRENT_TIMESTAMP() as loaded_at
    from source
)

select * from renamed
