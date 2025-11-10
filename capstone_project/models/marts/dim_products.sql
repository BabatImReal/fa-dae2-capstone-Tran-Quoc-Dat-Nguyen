{{ config(
  materialized='table',
  schema='sc_analytics',
  cluster_by=['product_category_name_english']
) }}

with stg_products as (
    select
        product_id,
        product_name_length,
        product_description_length,
        product_photos_qty,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm,
        loaded_at,
        is_current,
        effective_from,
        effective_to
    from {{ ref('stg__products') }}
),

int_products as (
    select
        product_id,
        product_category_name_english
    from {{ ref('int__products') }}
)

select
    -- surrogate key (includes effective_from for SCD Type 2)
    {{ dbt_utils.generate_surrogate_key(['sp.product_id', 'sp.effective_from']) }} as product_key,

    -- natural/business keys
    sp.product_id,

    -- category from int__products (enriched with English translation)
    ip.product_category_name_english,

    -- product attributes from stg__products
    sp.product_name_length,
    sp.product_description_length,
    sp.product_photos_qty,
    sp.product_weight_g,
    sp.product_length_cm,
    sp.product_height_cm,
    sp.product_width_cm,

    -- SCD Type 2 attributes
    sp.is_current,
    sp.effective_from,
    sp.effective_to,

    -- metadata
    sp.loaded_at,
    current_timestamp() as dbt_updated_at

from stg_products as sp
left join int_products as ip
    on sp.product_id = ip.product_id
