{{ config(
  materialized='table',
  cluster_by=['seller_state', 'seller_city']
) }}

with src as (
  select
    *
  from {{ ref('stg__sellers') }}
)
select
  {{ dbt_utils.generate_surrogate_key(['seller_id']) }} as seller_key,
  s.seller_id,
  s.seller_zip_code_prefix,
  s.seller_city,
  s.seller_state,
  s.loaded_at
  -- add any additional staged columns here if present
  -- , s.<other_column>
from src s
