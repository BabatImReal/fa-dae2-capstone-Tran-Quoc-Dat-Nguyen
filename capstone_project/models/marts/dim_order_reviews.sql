{{ config(
  materialized='table',
  cluster_by=['review_creation_date', 'review_score']
) }}

with src as (
  select
    *
  from {{ ref('stg__order_reviews') }}
)

select
  {{ dbt_utils.generate_surrogate_key(['review_id']) }} as order_review_key,
  review_id,
  order_id,
  review_score,
  review_creation_date,
  review_answer_timestamp,
  -- metadata
  loaded_at,
  current_timestamp() as dbt_updated_at
from src
