{{ config(
  materialized='table',
  schema='sc_analytics',
  cluster_by=['seller_state', 'seller_city']
) }}

with snapshot_src as (
    select *
    from {{ ref('stg__sellers') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['seller_id', 'dbt_valid_from']) }} as seller_key,
    seller_id,
    seller_zip_code_prefix,
    seller_city,
    seller_state,
    dbt_valid_from as effective_from,
    dbt_valid_to as effective_to,
    case when dbt_valid_to is null then true else false end as is_current,
    loaded_at
from snapshot_src
