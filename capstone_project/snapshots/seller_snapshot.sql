{% snapshot sellers_snapshot %}
{{
  config(
    target_schema='snapshots',
    unique_key='seller_id',
    strategy='check',
    check_cols=['seller_zip_code_prefix','seller_city','seller_state'],
    invalidate_hard_deletes=true
  )
}}
    select
        seller_id,
        seller_zip_code_prefix,
        seller_city,
        seller_state,
        loaded_at
    from {{ source('sc_raw_data', 'olist_sellers') }}
{% endsnapshot %}
