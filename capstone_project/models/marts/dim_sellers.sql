{{ config(
  materialized='table',
  schema='sc_analytics',
  cluster_by=['seller_state', 'seller_city']
) }}

with src as (
    select *
    from {{ ref('stg__sellers') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['seller_id', 'loaded_at']) }} as seller_key,
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state,
    loaded_at
-- add any additional staged columns here if present
-- , s.<other_column>
from src
