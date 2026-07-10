-- models/intermediate/int_sales_enriched.sql
-- ============================================================
-- Intermediate: Enriched Sales
-- Joins fact_sales with all dimension tables in one place.
-- All marts that need sales data pull from this model.
-- Author: Uday Mourya
-- ============================================================

with sales as (
    select * from {{ ref('stg_sales') }}
),

customers as (
    select * from {{ ref('stg_customers') }}
),

products as (
    select * from {{ ref('stg_products') }}
),

stores as (
    select * from {{ ref('stg_stores') }}
),

date_dim as (
    select * from {{ source('warehouse', 'dim_date') }}
),

enriched as (

    select
        -- ── Sale identifiers ───────────────────────────────────
        s.sale_key,
        s.order_id,
        s.order_line_id,

        -- ── Date attributes ────────────────────────────────────
        d.full_date         as order_date,
        d.year              as order_year,
        d.month_num         as order_month,
        d.month_name        as order_month_name,
        d.quarter           as order_quarter,
        d.week_number       as order_week,
        d.day_of_week       as order_day_of_week,
        d.is_weekend,
        d.is_uk_public_holiday,
        d.is_promotional    as is_promotional_period,
        d.season,

        -- ── Customer attributes ────────────────────────────────
        c.customer_id,
        c.age_band,
        c.gender,
        c.region            as customer_region,
        c.city              as customer_city,
        c.loyalty_tier,
        c.acquisition_channel,
        c.rfm_segment,
        c.customer_ltv_gbp,

        -- ── Product attributes ─────────────────────────────────
        p.product_id,
        p.product_name,
        p.category,
        p.subcategory,
        p.brand,
        p.supplier_id,
        p.rrp_gbp,

        -- ── Store attributes ───────────────────────────────────
        st.store_id,
        st.store_name,
        st.store_type,
        st.region           as store_region,
        st.city             as store_city,

        -- ── Measures ───────────────────────────────────────────
        s.units_sold,
        s.gross_revenue_gbp,
        s.discount_gbp,
        s.net_revenue_gbp,
        s.cost_of_goods_gbp,
        s.gross_profit_gbp,
        s.gross_margin_pct,

        -- ── Derived fields ─────────────────────────────────────
        s.net_revenue_gbp / nullif(s.units_sold, 0)  as revenue_per_unit,
        s.discount_gbp    / nullif(s.gross_revenue_gbp, 0) * 100
                                                     as discount_pct,

        -- ── Return flags ───────────────────────────────────────
        s.is_returned,
        s.return_date_key,

        -- ── Audit ──────────────────────────────────────────────
        s.pipeline_run_id

    from sales          s
    left join customers c  on s.customer_key = c.customer_key
    left join products  p  on s.product_key  = p.product_key
    left join stores    st on s.store_key    = st.store_key
    left join date_dim  d  on s.date_key     = d.date_key

)

select * from enriched
