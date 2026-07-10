-- models/marts/mart_store_performance.sql
-- ============================================================
-- Mart: Store Performance (Monthly)
-- One row per store per month.
-- Powers: store comparison table, regional heatmap.
-- Author: Uday Mourya
-- ============================================================

with monthly_store as (

    select
        store_id,
        store_name,
        store_type,
        store_region,
        store_city,
        order_year,
        order_month,
        order_month_name,

        -- Revenue
        round(sum(net_revenue_gbp), 2)              as revenue_gbp,
        round(sum(gross_profit_gbp), 2)             as gross_profit_gbp,
        round(sum(discount_gbp), 2)                 as discount_gbp,
        round(
            sum(gross_profit_gbp) * 100.0 / nullif(sum(net_revenue_gbp), 0), 2
        )                                           as gross_margin_pct,

        -- Volume
        count(distinct order_id)                    as total_orders,
        sum(units_sold)                             as total_units,
        count(distinct customer_id)                 as unique_customers,

        -- AOV
        round(
            sum(net_revenue_gbp) / nullif(count(distinct order_id), 0), 2
        )                                           as avg_order_value_gbp,

        -- Returns
        round(
            countif(is_returned) * 100.0 / count(*), 2
        )                                           as return_rate_pct

    from {{ ref('int_sales_enriched') }}
    group by 1, 2, 3, 4, 5, 6, 7, 8

),

-- Rank stores within each month by revenue
ranked as (

    select
        *,
        rank() over (
            partition by order_year, order_month
            order by revenue_gbp desc
        )                                           as revenue_rank_in_month

    from monthly_store

)

select * from ranked
order by order_year desc, order_month desc, revenue_rank_in_month
