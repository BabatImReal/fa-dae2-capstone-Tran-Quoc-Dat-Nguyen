{{ config(materialized='view') }}

with source as (
    select * from {{ source('sc_raw_data', 'olist_geolocation') }}
),

renamed as (
    select
        CAST(geolocation_zip_code_prefix as VARCHAR) as geolocation_zip_code_prefix,
        CAST(geolocation_lat as NUMBER(12, 8)) as geolocation_lat,
        CAST(geolocation_lng as NUMBER(12, 8)) as geolocation_lng,
        CAST(geolocation_city as VARCHAR) as geolocation_city,
        CAST(geolocation_state as VARCHAR) as geolocation_state,
        CAST(loaded_at as TIMESTAMP_NTZ) as loaded_at,
        CAST(source_system as VARCHAR) as source_system
    from source
)

select * from renamed
