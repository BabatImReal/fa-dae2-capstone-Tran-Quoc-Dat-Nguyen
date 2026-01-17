{{ config(materialized='ephemeral') }}

with products as (
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
        loaded_at,
        source_system,
        dbt_valid_from,
        dbt_valid_to
    from {{ ref('products_snapshot') }}
    where dbt_valid_to is null  -- Get only current records
),

product_category_translation as (
    select *
    from {{ ref('stg__product_category_name_translation') }}
),

-- Remove only products that have ALL attributes null (completely invalid)
cleaned_products as (
    select
        p.*,
        pct.product_category_name_english
    from products as p
    left join product_category_translation as pct
        on p.product_category_name = pct.product_category_name
    where
        -- Must have product_id (primary key)
        p.product_id is not null
        -- Must have at least ONE valid attribute (not all NULL)
        and p.product_category_name is not null
        and p.product_name_length is not null
        and p.product_description_length is not null
        and p.product_photos_qty is not null
        and p.product_weight_g is not null
        and p.product_length_cm is not null
        and p.product_height_cm is not null
        and p.product_width_cm is not null
        and pct.product_category_name_english is not null  -- Must have translation
)

select * from cleaned_products
