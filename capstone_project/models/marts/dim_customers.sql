{{ config(
    materialized='table',
    schema='sc_analytics',
    cluster_by=['customer_state', 'customer_city']
) }}

with snap as (
    select
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state,
        effective_from,
        effective_to,
        loaded_at,
        is_current
    from {{ ref('stg__customers') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['snap.customer_id', 'snap.effective_from']) }} as customer_key,
    snap.customer_id,
    snap.customer_unique_id,
    snap.customer_zip_code_prefix,
    snap.customer_city,
    snap.customer_state,

    -- SCD Type 2 attributes
    snap.is_current,
    snap.effective_from,
    snap.effective_to,

    -- Metadata
    snap.loaded_at
from snap
