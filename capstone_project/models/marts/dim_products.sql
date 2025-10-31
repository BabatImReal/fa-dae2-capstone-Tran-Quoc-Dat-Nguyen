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
        loaded_at
    from {{ ref('stg__products') }}
),

int_products as (
    select
        product_id,
        product_category_name_english
    from {{ ref('int__products') }}
)

select
    -- surrogate key
    {{ dbt_utils.generate_surrogate_key(['sp.product_id', 'sp.loaded_at']) }} as product_key,
    
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
    
    -- metadata
    sp.loaded_at,
    current_timestamp() as dbt_updated_at

from stg_products as sp
left join int_products as ip
    on sp.product_id = ip.product_id