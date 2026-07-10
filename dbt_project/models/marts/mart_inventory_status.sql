-- models/marts/mart_inventory_status.sql
-- ============================================================
-- Mart: Inventory Status (Latest Snapshot)
-- One row per product per store — most recent day only.
-- Powers: inventory RAG dashboard, daily stockout alert email.
-- Author: Uday Mourya
-- ============================================================

with latest_inventory as (

    select
        i.*,
        row_number() over (
            partition by i.product_key, i.store_key
            order by i.date_key desc
        ) as rn

    from {{ ref('stg_inventory') }} i

),

current_snapshot as (

    select
        i.inventory_key,
        i.date_key,
        p.product_id,
        p.product_name,
        p.category,
        p.subcategory,
        p.supplier_id,
        st.store_id,
        st.store_name,
        st.store_type,
        st.store_region,

        -- Stock levels
        i.stock_on_hand,
        i.units_received,
        i.units_sold,
        i.reorder_point,
        i.reorder_quantity,
        i.stock_status,
        i.days_of_stock_remaining,

        -- Enriched flags
        i.stock_on_hand <= 0                        as is_out_of_stock,
        i.stock_on_hand <= i.reorder_point          as needs_reorder,
        i.stock_on_hand - i.reorder_point           as stock_above_reorder,

        -- Potential lost revenue if out of stock
        round(
            greatest(i.reorder_point - i.stock_on_hand, 0)
            * coalesce(p.rrp_gbp, 0), 2
        )                                           as potential_lost_revenue_gbp

    from latest_inventory           i
    join {{ ref('stg_products') }}  p  on i.product_key = p.product_key
    join {{ ref('stg_stores') }}    st on i.store_key   = st.store_key
    where i.rn = 1

)

select * from current_snapshot
order by
    case stock_status when 'RED' then 1 when 'AMBER' then 2 else 3 end,
    days_of_stock_remaining asc
