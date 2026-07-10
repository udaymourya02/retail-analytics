-- models/marts/mart_product_performance.sql
-- ============================================================
-- Mart: Product Performance (Weekly)
-- One row per product per week.
-- Powers: top products table, category trend chart.
-- Author: Uday Mourya
-- ============================================================

with weekly_product as (

    select
        product_id,
        product_name,
        category,
        subcategory,
        brand,
        rrp_gbp,
        order_year,
        order_week,

        -- Revenue
        round(sum(net_revenue_gbp), 2)              as revenue_gbp,
        round(sum(gross_profit_gbp), 2)             as gross_profit_gbp,
        round(
            sum(gross_profit_gbp) * 100.0 / nullif(sum(net_revenue_gbp), 0), 2
        )                                           as gross_margin_pct,

        -- Volume
        sum(units_sold)                             as units_sold,
        count(distinct order_id)                    as orders_containing_product,
        count(distinct customer_id)                 as unique_buyers,

        -- Average selling price vs RRP
        round(sum(net_revenue_gbp) / nullif(sum(units_sold), 0), 2)
                                                    as avg_selling_price_gbp,
        round(
            (rrp_gbp - sum(net_revenue_gbp) / nullif(sum(units_sold), 0))
            * 100.0 / nullif(rrp_gbp, 0), 1
        )                                           as avg_discount_vs_rrp_pct,

        -- Channel split
        round(sum(case when store_type = 'Online'   then net_revenue_gbp else 0 end), 2)
                                                    as online_revenue_gbp,
        round(sum(case when store_type = 'Physical' then net_revenue_gbp else 0 end), 2)
                                                    as instore_revenue_gbp

    from {{ ref('int_sales_enriched') }}
    where is_returned = false
    group by 1, 2, 3, 4, 5, 6, 7, 8

),

ranked as (

    select
        *,
        rank() over (
            partition by order_year, order_week, category
            order by revenue_gbp desc
        )                                           as rank_in_category

    from weekly_product

)

select * from ranked
order by order_year desc, order_week desc, revenue_gbp desc
