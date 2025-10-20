-- ephemeral canonical products
{{ config(materialized='ephemeral') }}

select
  {{ dbt_utils.generate_surrogate_key(['product_id']) }} as product_sk,
  p.product_id,
  p.product_name_length,
  p.product_description_length,
  p.product_photos_qty,
  p.product_weight_g,
  p.product_length_cm,
  p.product_height_cm,
  p.product_width_cm,
  coalesce(t.product_category_name_english, p.product_category_name) as product_category_english,
  p.loaded_at
from {{ ref('stg__products') }} p
left join {{ ref('stg__product_category_name_translation') }} t
  on p.product_category_name = t.product_category_name
;