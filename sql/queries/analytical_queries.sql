-- ============================================================
-- ANALYTICAL QUERIES — RetailCo Analytics Platform
-- Author: Uday Mourya
-- These queries power dashboard visuals and ad hoc analysis
-- ============================================================


-- ------------------------------------------------------------
-- Q1: Daily Revenue Summary (last 30 days)
-- Powers: Executive KPI dashboard — revenue trend chart
-- ------------------------------------------------------------
SELECT
    d.full_date,
    d.day_of_week,
    d.is_weekend,
    COUNT(DISTINCT s.order_id)                          AS total_orders,
    SUM(s.units_sold)                                   AS total_units,
    ROUND(SUM(s.net_revenue_pence) / 100.0, 2)         AS net_revenue_gbp,
    ROUND(SUM(s.gross_profit_pence) / 100.0, 2)        AS gross_profit_gbp,
    ROUND(
        SUM(s.gross_profit_pence) * 100.0 / NULLIF(SUM(s.net_revenue_pence), 0),
        1
    )                                                   AS gross_margin_pct,
    ROUND(
        SUM(s.net_revenue_pence) / 100.0 / NULLIF(COUNT(DISTINCT s.order_id), 0),
        2
    )                                                   AS avg_order_value_gbp
FROM `retailco.warehouse.fact_sales`    s
JOIN `retailco.warehouse.dim_date`      d ON s.date_key = d.date_key
WHERE d.full_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
  AND s.is_returned = FALSE
GROUP BY 1, 2, 3
ORDER BY 1 DESC;


-- ------------------------------------------------------------
-- Q2: Revenue by Store (MTD, with prior month comparison)
-- Powers: Store performance table and heatmap
-- ------------------------------------------------------------
WITH current_month AS (
    SELECT
        st.store_id,
        st.store_name,
        st.region,
        st.city,
        ROUND(SUM(s.net_revenue_pence) / 100.0, 2)     AS revenue_gbp,
        COUNT(DISTINCT s.order_id)                      AS orders,
        COUNT(DISTINCT s.customer_key)                  AS unique_customers
    FROM `retailco.warehouse.fact_sales`    s
    JOIN `retailco.warehouse.dim_store`     st ON s.store_key = st.store_key
    JOIN `retailco.warehouse.dim_date`      d  ON s.date_key  = d.date_key
    WHERE d.year = EXTRACT(YEAR FROM CURRENT_DATE())
      AND d.month_num = EXTRACT(MONTH FROM CURRENT_DATE())
      AND s.is_returned = FALSE
    GROUP BY 1, 2, 3, 4
),
prior_month AS (
    SELECT
        st.store_id,
        ROUND(SUM(s.net_revenue_pence) / 100.0, 2)     AS revenue_gbp_prior
    FROM `retailco.warehouse.fact_sales`    s
    JOIN `retailco.warehouse.dim_store`     st ON s.store_key = st.store_key
    JOIN `retailco.warehouse.dim_date`      d  ON s.date_key  = d.date_key
    WHERE d.full_date BETWEEN
        DATE_TRUNC(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH), MONTH)
        AND LAST_DAY(DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH))
      AND s.is_returned = FALSE
    GROUP BY 1
)
SELECT
    c.store_id,
    c.store_name,
    c.region,
    c.city,
    c.revenue_gbp,
    c.orders,
    c.unique_customers,
    p.revenue_gbp_prior,
    ROUND(
        (c.revenue_gbp - p.revenue_gbp_prior) * 100.0
        / NULLIF(p.revenue_gbp_prior, 0),
        1
    )                                                   AS mom_growth_pct
FROM current_month  c
LEFT JOIN prior_month p ON c.store_id = p.store_id
ORDER BY c.revenue_gbp DESC;


-- ------------------------------------------------------------
-- Q3: Top 10 Products by Revenue (last 28 days)
-- Powers: Executive dashboard top products table
-- ------------------------------------------------------------
SELECT
    p.product_id,
    p.product_name,
    p.category,
    p.subcategory,
    SUM(s.units_sold)                                   AS units_sold,
    ROUND(SUM(s.net_revenue_pence) / 100.0, 2)         AS revenue_gbp,
    ROUND(SUM(s.gross_profit_pence) / 100.0, 2)        AS profit_gbp,
    ROUND(
        SUM(s.gross_profit_pence) * 100.0 / NULLIF(SUM(s.net_revenue_pence), 0),
        1
    )                                                   AS margin_pct
FROM `retailco.warehouse.fact_sales`    s
JOIN `retailco.warehouse.dim_product`   p ON s.product_key = p.product_key
JOIN `retailco.warehouse.dim_date`      d ON s.date_key    = d.date_key
WHERE d.full_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 28 DAY)
  AND s.is_returned = FALSE
GROUP BY 1, 2, 3, 4
ORDER BY revenue_gbp DESC
LIMIT 10;


-- ------------------------------------------------------------
-- Q4: Customer RFM Segment Distribution (current week)
-- Powers: Customer Intelligence dashboard segment chart
-- ------------------------------------------------------------
SELECT
    rfm_segment,
    COUNT(*)                                            AS customer_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct_of_base,
    ROUND(AVG(customer_ltv_gbp), 2)                    AS avg_ltv_gbp,
    ROUND(SUM(customer_ltv_gbp), 2)                    AS total_ltv_gbp
FROM `retailco.warehouse.dim_customer`
WHERE is_current = TRUE
  AND rfm_segment IS NOT NULL
GROUP BY 1
ORDER BY total_ltv_gbp DESC;


-- ------------------------------------------------------------
-- Q5: Inventory Stockout Risk Report
-- Powers: Inventory dashboard RAG table + daily alert email
-- ------------------------------------------------------------
SELECT
    p.product_id,
    p.product_name,
    p.category,
    st.store_name,
    st.region,
    i.stock_on_hand,
    i.reorder_point,
    i.reorder_quantity,
    i.stock_status,
    i.days_of_stock_remaining,
    -- Forecasted demand next 7 days (from forecasting mart)
    f.forecast_units_7d
FROM `retailco.warehouse.fact_inventory`    i
JOIN `retailco.warehouse.dim_product`       p  ON i.product_key = p.product_key
JOIN `retailco.warehouse.dim_store`         st ON i.store_key   = st.store_key
-- Join to forecasting output (built by Prophet model)
LEFT JOIN (
    SELECT product_id, SUM(forecast_units) AS forecast_units_7d
    FROM `retailco.warehouse.mart_demand_forecast`
    WHERE forecast_date BETWEEN CURRENT_DATE() AND DATE_ADD(CURRENT_DATE(), INTERVAL 7 DAY)
    GROUP BY product_id
) f ON p.product_id = f.product_id
WHERE i.date_key = CAST(FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)) AS INT64)
  AND i.stock_status IN ('RED', 'AMBER')
ORDER BY
    CASE i.stock_status WHEN 'RED' THEN 1 WHEN 'AMBER' THEN 2 END,
    i.days_of_stock_remaining ASC;


-- ------------------------------------------------------------
-- Q6: Marketing Channel Attribution Summary
-- Powers: Marketing attribution dashboard
-- ------------------------------------------------------------
SELECT
    c.channel                                           AS marketing_channel,
    COUNT(DISTINCT m.campaign_key)                      AS active_campaigns,
    SUM(m.impressions)                                  AS impressions,
    SUM(m.clicks)                                       AS clicks,
    ROUND(SUM(m.clicks) * 100.0 / NULLIF(SUM(m.impressions), 0), 2)
                                                        AS ctr_pct,
    ROUND(SUM(m.spend_pence) / 100.0, 2)               AS spend_gbp,
    ROUND(SUM(m.attributed_revenue_pence) / 100.0, 2)  AS attributed_revenue_gbp,
    SUM(m.attributed_orders)                            AS attributed_orders,
    ROUND(
        SUM(m.attributed_revenue_pence) / NULLIF(SUM(m.spend_pence), 0),
        2
    )                                                   AS roas,
    ROUND(
        SUM(m.spend_pence) / 100.0 / NULLIF(SUM(m.attributed_orders), 0),
        2
    )                                                   AS cost_per_order_gbp
FROM `retailco.warehouse.fact_marketing_spend`  m
JOIN `retailco.warehouse.dim_campaign`           c ON m.campaign_key = c.campaign_key
JOIN `retailco.warehouse.dim_date`               d ON m.date_key     = d.date_key
WHERE d.full_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
GROUP BY 1
ORDER BY attributed_revenue_gbp DESC;


-- ------------------------------------------------------------
-- Q7: New vs Returning Customer Split (last 12 months, monthly)
-- Powers: Customer acquisition trend chart
-- ------------------------------------------------------------
SELECT
    d.year,
    d.month_num,
    d.month_name,
    COUNT(DISTINCT CASE
        WHEN c.acquisition_date >= DATE_TRUNC(d.full_date, MONTH)
         AND c.acquisition_date <  DATE_ADD(DATE_TRUNC(d.full_date, MONTH), INTERVAL 1 MONTH)
        THEN s.customer_key
    END)                                                AS new_customers,
    COUNT(DISTINCT CASE
        WHEN c.acquisition_date < DATE_TRUNC(d.full_date, MONTH)
        THEN s.customer_key
    END)                                                AS returning_customers,
    COUNT(DISTINCT s.customer_key)                      AS total_customers
FROM `retailco.warehouse.fact_sales`    s
JOIN `retailco.warehouse.dim_date`      d ON s.date_key      = d.date_key
JOIN `retailco.warehouse.dim_customer`  c ON s.customer_key  = c.customer_key
WHERE d.full_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 12 MONTH)
  AND s.is_returned = FALSE
  AND c.is_current  = TRUE
GROUP BY 1, 2, 3
ORDER BY 1, 2;


-- ------------------------------------------------------------
-- Q8: Data Pipeline Health Check
-- Powers: Data quality monitoring dashboard
-- ------------------------------------------------------------
SELECT
    run_date,
    source_system,
    status,
    records_extracted,
    records_loaded,
    records_quarantined,
    ROUND(records_quarantined * 100.0 / NULLIF(records_extracted, 0), 2)
                                                        AS quarantine_rate_pct,
    duration_seconds,
    error_message
FROM `retailco.warehouse.pipeline_run_log`
WHERE run_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY run_date DESC, source_system;
