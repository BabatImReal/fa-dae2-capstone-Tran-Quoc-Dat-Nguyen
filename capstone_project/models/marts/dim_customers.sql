{{ config(
    materialized='table',
    cluster_by=['customer_state', 'customer_city']
) }}

with src as (
  select
    *
  from {{ ref('stg__customers') }}
)

select
  {{ dbt_utils.generate_surrogate_key(['customer_id']) }} as customer_key,
  customer_id,
  customer_unique_id,
  customer_zip_code_prefix,
  customer_city,
  customer_state,
  -- Processing metadata
  loaded_at,
  CURRENT_TIMESTAMP() as dbt_updated_at,
from src
