{% snapshot order_reviews_snapshot %}
{{
  config(
    target_schema='snapshots',
    unique_key=['review_id', 'order_id'],
    strategy='check',
    check_cols=['review_score', 'review_comment_title', 'review_comment_message', 'review_creation_date', 'review_answer_timestamp'],
    invalidate_hard_deletes=true
  )
}}
select
    review_id,
    order_id,
    review_score,
    review_comment_title,
    review_comment_message,
    review_creation_date,
    review_answer_timestamp,
    loaded_at
from {{ source('sc_raw_data', 'olist_order_reviews') }}
{% endsnapshot %}
