{{ config(
  materialized='table',
  schema='sc_analytics',
  cluster_by=['seller_state', 'seller_city']
) }}

with snapshot_src as (
    select
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state,
        dbt_valid_from as effective_from,
        dbt_valid_to as effective_to,
        loaded_at,
        (dbt_valid_to is null) as is_current
    from {{ ref('int__sellers') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['seller_id', 'effective_from']) }} as seller_key,
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state,
    effective_from,
    effective_to,
    is_current,
    loaded_at
from snapshot_src
