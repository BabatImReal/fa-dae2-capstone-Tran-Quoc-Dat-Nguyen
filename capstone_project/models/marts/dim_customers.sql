{{ config(
    materialized='table',
    cluster_by=['customer_state', 'customer_city']
) }}

with snap as (
  select
    customer_id,
    customer_unique_id,
    customer_zip_code_prefix,
    customer_city,
    customer_state,
    dbt_valid_from as effective_from,
    dbt_valid_to   as effective_to,
    (dbt_valid_to is null) as is_current,
    loaded_at
  from {{ ref('customers_snapshot') }}
)

select
  {{ dbt_utils.generate_surrogate_key(['customer_id', 'effective_from']) }} as customer_key,
  customer_id,
  customer_unique_id,
  customer_zip_code_prefix,
  customer_city,
  customer_state,
  is_current,
  effective_from,
  effective_to,     -- stays NULL for the latest/current row
  loaded_at
from snap
-- Optional: helps in queries, CTAS order not guaranteed by all warehouses
-- order by is_current desc, effective_from desc