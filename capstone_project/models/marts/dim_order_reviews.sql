{{ config(
  materialized='table',
  schema='sc_analytics',
  cluster_by=['review_creation_date', 'review_score']
) }}

with src as (
    select *
    from {{ ref('stg__order_reviews') }}
)

select
    -- surrogate key (includes effective_from for SCD Type 2)
    {{ dbt_utils.generate_surrogate_key(['review_id', 'order_id', 'effective_from']) }} as order_review_key,
    review_id,
    order_id,
    review_score,
    review_creation_date,
    review_answer_timestamp,

    -- SCD Type 2 attributes
    is_current,
    effective_from,
    effective_to,

    -- metadata
    loaded_at
from src
