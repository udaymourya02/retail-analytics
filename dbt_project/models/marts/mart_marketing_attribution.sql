-- models/marts/mart_marketing_attribution.sql
-- ============================================================
-- Mart: Marketing Attribution (Monthly by Channel)
-- One row per campaign per month.
-- Powers: marketing attribution dashboard, ROAS chart.
-- Author: Uday Mourya
-- ============================================================

with spend as (
    select * from {{ ref('stg_marketing_spend') }}
),

campaigns as (
    select * from {{ source('warehouse', 'dim_campaign') }}
),

date_dim as (
    select * from {{ source('warehouse', 'dim_date') }}
),

monthly_attribution as (

    select
        d.year,
        d.month_num,
        d.month_name,
        c.campaign_id,
        c.campaign_name,
        c.channel                               as marketing_channel,
        c.objective,

        -- Spend metrics
        round(sum(s.spend_gbp), 2)              as total_spend_gbp,
        sum(s.impressions)                      as total_impressions,
        sum(s.clicks)                           as total_clicks,

        -- Performance metrics
        round(sum(s.clicks) * 100.0 / nullif(sum(s.impressions), 0), 3)
                                                as ctr_pct,
        round(sum(s.spend_gbp) / nullif(sum(s.clicks), 0), 4)
                                                as avg_cpc_gbp,

        -- Attribution
        round(sum(s.attributed_revenue_gbp), 2) as attributed_revenue_gbp,
        sum(s.attributed_orders)                as attributed_orders,

        -- ROAS (Return on Ad Spend)
        round(
            sum(s.attributed_revenue_gbp) / nullif(sum(s.spend_gbp), 0), 2
        )                                       as roas,

        -- Cost per order
        round(
            sum(s.spend_gbp) / nullif(sum(s.attributed_orders), 0), 2
        )                                       as cost_per_order_gbp,

        -- Revenue share
        round(
            sum(s.attributed_revenue_gbp) * 100.0
            / nullif(sum(sum(s.attributed_revenue_gbp)) over (partition by d.year, d.month_num), 0),
            2
        )                                       as revenue_share_pct

    from spend      s
    join campaigns  c on s.campaign_key = c.campaign_key
    join date_dim   d on s.date_key     = d.date_key
    group by 1, 2, 3, 4, 5, 6, 7

)

select * from monthly_attribution
order by year desc, month_num desc, total_spend_gbp desc
