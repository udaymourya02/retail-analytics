-- models/marts/mart_executive_kpis.sql
-- ============================================================
-- Mart: Executive KPI Daily Summary
-- One row per day. Powers the executive dashboard in Power BI.
-- Includes WoW and YoY comparisons for every metric.
-- Author: Uday Mourya
-- ============================================================

with daily_sales as (

    select
        order_date,
        order_year,
        order_month,
        order_month_name,
        order_quarter,
        order_week,
        is_weekend,
        is_promotional_period,
        season,

        -- Revenue metrics
        round(sum(net_revenue_gbp), 2)          as revenue_gbp,
        round(sum(gross_profit_gbp), 2)         as gross_profit_gbp,
        round(sum(discount_gbp), 2)             as discount_gbp,

        -- Volume metrics
        count(distinct order_id)                as total_orders,
        sum(units_sold)                         as total_units,
        count(distinct customer_id)             as unique_customers,

        -- Average metrics
        round(
            sum(net_revenue_gbp) / nullif(count(distinct order_id), 0),
            2
        )                                       as avg_order_value_gbp,

        -- Margin
        round(
            sum(gross_profit_gbp) * 100.0 / nullif(sum(net_revenue_gbp), 0),
            2
        )                                       as gross_margin_pct,

        -- Return metrics
        countif(is_returned = true)             as returned_lines,
        round(sum(case when is_returned then net_revenue_gbp else 0 end), 2)
                                                as returned_revenue_gbp,

        -- Channel split
        round(sum(case when store_type = 'Online'   then net_revenue_gbp else 0 end), 2)
                                                as online_revenue_gbp,
        round(sum(case when store_type = 'Physical' then net_revenue_gbp else 0 end), 2)
                                                as instore_revenue_gbp,

        -- New vs returning customers
        countif(acquisition_channel is not null
            and date_diff(order_date, last_purchase_date, day) < 1)
                                                as new_customer_orders

    from {{ ref('int_sales_enriched') }}
    where order_date >= date('{{ var("start_date") }}')
    group by 1, 2, 3, 4, 5, 6, 7, 8, 9

),

-- ── Add WoW and YoY comparisons ──────────────────────────────────────────

with_comparisons as (

    select
        current_day.*,

        -- Week-on-week: same metric 7 days ago
        prior_week.revenue_gbp          as revenue_gbp_wow,
        prior_week.total_orders         as orders_wow,
        prior_week.avg_order_value_gbp  as aov_wow,

        -- Year-on-year: same calendar date last year
        prior_year.revenue_gbp          as revenue_gbp_yoy,
        prior_year.total_orders         as orders_yoy,

        -- Growth % calculations
        round(
            (current_day.revenue_gbp - prior_week.revenue_gbp) * 100.0
            / nullif(prior_week.revenue_gbp, 0), 1
        )                               as revenue_growth_wow_pct,

        round(
            (current_day.revenue_gbp - prior_year.revenue_gbp) * 100.0
            / nullif(prior_year.revenue_gbp, 0), 1
        )                               as revenue_growth_yoy_pct,

        round(
            (current_day.total_orders - prior_week.total_orders) * 100.0
            / nullif(prior_week.total_orders, 0), 1
        )                               as orders_growth_wow_pct

    from daily_sales                current_day
    left join daily_sales           prior_week
        on prior_week.order_date = date_sub(current_day.order_date, interval 7 day)
    left join daily_sales           prior_year
        on prior_year.order_date = date_sub(current_day.order_date, interval 364 day)

)

select * from with_comparisons
order by order_date desc
