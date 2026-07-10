-- models/staging/stg_sales.sql
-- ============================================================
-- Staging: Sales
-- Source  : retailco.warehouse.fact_sales (raw ETL output)
-- Purpose : Rename columns, cast types, apply zero business logic
-- Author  : Uday Mourya
-- ============================================================

with source as (

    select * from {{ source('warehouse', 'fact_sales') }}

),

renamed as (

    select
        -- Keys
        sale_key,
        order_id,
        order_line_id,
        date_key,
        customer_key,
        product_key,
        store_key,
        channel_key,
        campaign_key,

        -- Measures (convert pence → GBP at staging layer)
        units_sold,
        round(gross_revenue_pence / 100.0, 2)   as gross_revenue_gbp,
        round(discount_pence      / 100.0, 2)   as discount_gbp,
        round(net_revenue_pence   / 100.0, 2)   as net_revenue_gbp,
        round(cost_of_goods_pence / 100.0, 2)   as cost_of_goods_gbp,
        round(gross_profit_pence  / 100.0, 2)   as gross_profit_gbp,

        -- Derived margin % (safe divide)
        case
            when net_revenue_pence = 0 then null
            else round(gross_profit_pence * 100.0 / net_revenue_pence, 2)
        end                                      as gross_margin_pct,

        -- Return fields
        is_returned,
        return_date_key,

        -- Audit
        source_system,
        pipeline_run_id,
        created_at,
        updated_at

    from source
    where sale_key is not null   -- primary key must not be null

)

select * from renamed
