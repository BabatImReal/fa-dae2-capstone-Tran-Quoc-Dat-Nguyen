{{ config(
    materialized='view',
    schema='sc_staging') }}

with source as (
    select * from {{ ref('order_reviews_snapshot') }}
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
        'snapshot' as source_system,
        (dbt_valid_to is null) as is_current,
        dbt_valid_from as effective_from,
        dbt_valid_to as effective_to
    from source
)

select * from renamed
