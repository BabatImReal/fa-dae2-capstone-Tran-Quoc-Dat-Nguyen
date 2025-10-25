{{ config(
  materialized='table',
  schema='sc_analytics',
  cluster_by=['product_category_english']
) }}

with src as (
    select *
    from {{ ref('int__products') }}
)

select
    -- surrogate key
    {{ dbt_utils.generate_surrogate_key(['product_id', 'loaded_at']) }} as product_key,
    -- natural/business keys and attributes
    product_id,
    product_category_english,
    product_name_length,
    product_description_length,
    product_photos_qty,
    product_weight_g,
    product_length_cm,
    product_height_cm,
    product_width_cm,
    -- metadata
    loaded_at
from src
