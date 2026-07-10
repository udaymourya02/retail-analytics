-- models/staging/stg_inventory.sql
with source as (
    select * from {{ source('warehouse', 'fact_inventory') }}
),
renamed as (
    select
        inventory_key,
        date_key,
        product_key,
        store_key,
        stock_on_hand,
        units_received,
        units_sold,
        units_returned,
        reorder_point,
        reorder_quantity,
        stock_status,
        days_of_stock_remaining,
        source_system,
        pipeline_run_id,
        created_at
    from source
    where inventory_key is not null
)
select * from renamed
