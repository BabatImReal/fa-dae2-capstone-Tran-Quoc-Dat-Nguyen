{{ config(materialized='ephemeral') }}

with order_reviews as (
    select
        review_id,
        order_id,
        cast(review_score as number(38,0)) as review_score,
        review_comment_title,
        review_comment_message,
        review_creation_date,
        review_answer_timestamp,
        loaded_at,
        source_system,
        dbt_valid_from,
        dbt_valid_to
    from {{ ref('order_reviews_snapshot') }}
    where dbt_valid_to is null  -- Get only current records
)

select * from order_reviews
