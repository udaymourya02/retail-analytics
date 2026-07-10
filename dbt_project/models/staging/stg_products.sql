-- models/staging/stg_products.sql
with source as (
    select * from {{ source('warehouse', 'dim_product') }}
),
renamed as (
    select
        product_key,
        product_id,
        product_name,
        category,
        subcategory,
        brand,
        supplier_id,
        supplier_name,
        round(cost_price_pence / 100.0, 2)  as cost_price_gbp,
        round(rrp_pence        / 100.0, 2)  as rrp_gbp,
        is_active,
        launch_date,
        discontinue_date,
        is_current,
        valid_from,
        valid_to,
        created_at,
        updated_at
    from source
    where product_key is not null
      and is_current = true
)
select * from renamed
