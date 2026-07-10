-- models/intermediate/int_customer_orders.sql
-- ============================================================
-- Intermediate: Customer Order Summary
-- Aggregates all sales to one row per customer.
-- Used by: mart_customer_rfm, mart_customer_ltv
-- Author: Uday Mourya
-- ============================================================

with sales as (
    select * from {{ ref('int_sales_enriched') }}
    where is_returned = false     -- exclude returned items from value calculations
),

customer_orders as (

    select
        customer_id,
        customer_region,
        loyalty_tier,
        acquisition_channel,

        -- ── RFM inputs ─────────────────────────────────────────
        -- Recency: days since last purchase (lower = more recent = better)
        date_diff(current_date(), max(order_date), day)     as days_since_last_purchase,
        max(order_date)                                     as last_purchase_date,
        min(order_date)                                     as first_purchase_date,

        -- Frequency: number of distinct purchase dates
        count(distinct order_date)                          as purchase_frequency,
        count(distinct order_id)                            as total_orders,
        sum(units_sold)                                     as total_units_purchased,

        -- Monetary: total net revenue
        round(sum(net_revenue_gbp), 2)                      as total_revenue_gbp,
        round(avg(net_revenue_gbp), 2)                      as avg_order_value_gbp,
        round(sum(gross_profit_gbp), 2)                     as total_profit_gbp,

        -- ── Behaviour flags ────────────────────────────────────
        countif(is_weekend = true)                          as weekend_orders,
        countif(is_promotional_period = true)               as promo_orders,
        countif(store_type = 'Online')                      as online_orders,
        countif(store_type = 'Physical')                    as instore_orders,

        -- ── Category preferences ───────────────────────────────
        -- Top category by revenue (approximation via string_agg + mode)
        (
            select category
            from unnest(array_agg(struct(category, net_revenue_gbp)))
            group by category
            order by sum(net_revenue_gbp) desc
            limit 1
        )                                                   as top_category,

        -- ── Tenure ─────────────────────────────────────────────
        date_diff(current_date(), min(order_date), day)     as customer_age_days

    from sales
    group by 1, 2, 3, 4

)

select * from customer_orders
