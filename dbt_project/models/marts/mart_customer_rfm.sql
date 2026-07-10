-- models/marts/mart_customer_rfm.sql
-- ============================================================
-- Mart: Customer RFM Segmentation
-- Scores every customer 1–5 on Recency, Frequency, Monetary.
-- Assigns a named segment based on score combinations.
-- Refreshed weekly — powers the Customer Intelligence dashboard.
-- Author: Uday Mourya
-- ============================================================

with customer_orders as (
    select * from {{ ref('int_customer_orders') }}
),

-- ── Step 1: Calculate quintile boundaries for R, F, M ─────────────────────
-- NTILE(5) splits customers into 5 equal groups.
-- Recency: LOWER days = BETTER, so we invert (rank 5 = most recent)
-- Frequency and Monetary: HIGHER = BETTER, so rank 5 = highest

rfm_scores as (

    select
        customer_id,
        customer_region,
        loyalty_tier,
        acquisition_channel,
        top_category,
        last_purchase_date,
        first_purchase_date,
        days_since_last_purchase,
        purchase_frequency,
        total_orders,
        total_revenue_gbp,
        avg_order_value_gbp,
        total_profit_gbp,
        customer_age_days,
        online_orders,
        instore_orders,

        -- Recency score: invert so 5 = most recent (best)
        6 - ntile(5) over (order by days_since_last_purchase desc)  as r_score,

        -- Frequency score: 5 = highest frequency
        ntile(5) over (order by purchase_frequency asc)             as f_score,

        -- Monetary score: 5 = highest spend
        ntile(5) over (order by total_revenue_gbp asc)              as m_score

    from customer_orders

),

-- ── Step 2: Assign segment labels ─────────────────────────────────────────

segmented as (

    select
        *,

        -- RFM combined score (useful for sorting)
        (r_score + f_score + m_score)                               as rfm_total_score,

        -- Named segment — order matters: most specific rules first
        case
            when r_score >= 4 and f_score >= 4 and m_score >= 4
                then 'Champions'
            when r_score >= 3 and f_score >= 3 and m_score >= 3
                then 'Loyal Customers'
            when r_score >= 4 and f_score <= 2
                then 'New Customers'
            when r_score >= 3 and f_score >= 2 and m_score >= 2
                then 'Potential Loyalists'
            when r_score <= 2 and f_score >= 3 and m_score >= 3
                then 'At Risk'
            when r_score <= 2 and f_score >= 2
                then 'Needs Attention'
            when r_score = 1 and f_score <= 2
                then 'Lost'
            else 'Others'
        end                                                         as rfm_segment

    from rfm_scores

),

-- ── Step 3: Add segment metadata ──────────────────────────────────────────

final as (

    select
        -- Identity
        customer_id,
        customer_region,
        loyalty_tier,
        acquisition_channel,
        top_category,

        -- Purchase history
        first_purchase_date,
        last_purchase_date,
        days_since_last_purchase,
        purchase_frequency,
        total_orders,
        total_revenue_gbp,
        avg_order_value_gbp,
        total_profit_gbp,
        customer_age_days,

        -- Channel behaviour
        online_orders,
        instore_orders,
        round(online_orders  * 100.0 / nullif(total_orders, 0), 1)  as online_pct,
        round(instore_orders * 100.0 / nullif(total_orders, 0), 1)  as instore_pct,

        -- RFM scores
        r_score,
        f_score,
        m_score,
        rfm_total_score,
        rfm_segment,

        -- Segment priority for sorting (Champions first)
        case rfm_segment
            when 'Champions'          then 1
            when 'Loyal Customers'    then 2
            when 'Potential Loyalists'then 3
            when 'New Customers'      then 4
            when 'Needs Attention'    then 5
            when 'At Risk'            then 6
            when 'Lost'               then 7
            else 8
        end                                                          as segment_priority,

        -- Metadata
        current_timestamp()                                          as rfm_calculated_at,
        '{{ run_started_at }}'                                       as dbt_run_at

    from segmented

)

select * from final
