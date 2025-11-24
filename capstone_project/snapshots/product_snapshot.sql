{% snapshot products_snapshot %}
{{
  config(
    target_schema='snapshots',
    unique_key='product_id',
    strategy='check',
    check_cols=['product_category_name', 'product_name_length', 'product_description_length', 'product_photos_qty', 'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm'],
    invalidate_hard_deletes=true
  )
}}
    select
        product_id,
        product_category_name,
        product_name_length,
        product_description_length,
        product_photos_qty,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm,
        loaded_at
    from {{ source('sc_raw_data', 'olist_products') }}
{% endsnapshot %}
