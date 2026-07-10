-- models/staging/stg_stores.sql
with source as (
    select * from {{ source('warehouse', 'dim_store') }}
),
renamed as (
    select
        store_key,
        store_id,
        store_name,
        store_type,
        city,
        region,
        country,
        postcode,
        opening_date,
        is_active,
        is_current,
        valid_from,
        valid_to,
        created_at,
        updated_at
    from source
    where store_key is not null
      and is_current = true
)
select * from renamed
