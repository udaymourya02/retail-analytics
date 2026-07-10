-- ============================================================
-- FACT TABLES — RetailCo Analytics Platform
-- Target: Google BigQuery
-- Author: Uday Mourya
-- ============================================================

-- ------------------------------------------------------------
-- FACT_SALES: One row per order line item
-- Grain: 1 row = 1 product within 1 order
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `retailco.warehouse.fact_sales` (
    -- Surrogate key
    sale_key              INT64   NOT NULL,
    -- Natural keys (kept for debugging)
    order_id              STRING  NOT NULL,
    order_line_id         STRING  NOT NULL,
    -- Foreign keys to dimensions
    date_key              INT64   NOT NULL,   -- FK → dim_date
    customer_key          INT64   NOT NULL,   -- FK → dim_customer
    product_key           INT64   NOT NULL,   -- FK → dim_product
    store_key             INT64   NOT NULL,   -- FK → dim_store
    channel_key           INT64   NOT NULL,   -- FK → dim_channel
    campaign_key          INT64,              -- FK → dim_campaign (nullable)
    -- Measures (all monetary in pence)
    units_sold            INT64   NOT NULL,
    gross_revenue_pence   INT64   NOT NULL,   -- before discounts
    discount_pence        INT64   NOT NULL DEFAULT 0,
    net_revenue_pence     INT64   NOT NULL,   -- after discounts, excl. VAT
    cost_of_goods_pence   INT64   NOT NULL,
    gross_profit_pence    INT64   NOT NULL,   -- net_revenue - cost_of_goods
    -- Return flags
    is_returned           BOOL    NOT NULL DEFAULT FALSE,
    return_date_key       INT64,              -- FK → dim_date (if returned)
    -- Audit columns
    source_system         STRING  NOT NULL DEFAULT 'POS',
    pipeline_run_id       STRING  NOT NULL,
    created_at            TIMESTAMP NOT NULL,
    updated_at            TIMESTAMP NOT NULL
)
PARTITION BY RANGE_BUCKET(date_key, GENERATE_ARRAY(20200101, 20301231, 10000))
CLUSTER BY store_key, product_key;

-- ------------------------------------------------------------
-- FACT_INVENTORY: Daily snapshot per product per store
-- Grain: 1 row = 1 SKU × 1 store × 1 date
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `retailco.warehouse.fact_inventory` (
    inventory_key         INT64   NOT NULL,
    -- Foreign keys
    date_key              INT64   NOT NULL,   -- FK → dim_date
    product_key           INT64   NOT NULL,   -- FK → dim_product
    store_key             INT64   NOT NULL,   -- FK → dim_store
    -- Measures
    stock_on_hand         INT64   NOT NULL,   -- units at end of day
    units_received        INT64   NOT NULL DEFAULT 0,
    units_sold            INT64   NOT NULL DEFAULT 0,
    units_returned        INT64   NOT NULL DEFAULT 0,
    reorder_point         INT64   NOT NULL,
    reorder_quantity      INT64   NOT NULL,
    stock_status          STRING  NOT NULL,   -- 'RED','AMBER','GREEN'
    days_of_stock_remaining FLOAT64,          -- stock_on_hand / avg_daily_sales
    -- Audit
    source_system         STRING  NOT NULL DEFAULT 'WMS',
    pipeline_run_id       STRING  NOT NULL,
    created_at            TIMESTAMP NOT NULL
)
PARTITION BY RANGE_BUCKET(date_key, GENERATE_ARRAY(20200101, 20301231, 10000))
CLUSTER BY store_key, product_key;

-- ------------------------------------------------------------
-- FACT_MARKETING_SPEND: Daily marketing performance per campaign
-- Grain: 1 row = 1 campaign × 1 date
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `retailco.warehouse.fact_marketing_spend` (
    spend_key             INT64   NOT NULL,
    -- Foreign keys
    date_key              INT64   NOT NULL,   -- FK → dim_date
    campaign_key          INT64   NOT NULL,   -- FK → dim_campaign
    -- Measures
    impressions           INT64   NOT NULL DEFAULT 0,
    clicks                INT64   NOT NULL DEFAULT 0,
    spend_pence           INT64   NOT NULL DEFAULT 0,
    attributed_revenue_pence INT64 NOT NULL DEFAULT 0,
    attributed_orders     INT64   NOT NULL DEFAULT 0,
    -- Derived
    ctr                   FLOAT64,            -- clicks / impressions
    cpc_pence             INT64,              -- spend / clicks
    roas                  FLOAT64,            -- attributed_revenue / spend
    -- Audit
    source_system         STRING  NOT NULL,   -- 'Google Ads','Meta','Email'
    pipeline_run_id       STRING  NOT NULL,
    created_at            TIMESTAMP NOT NULL
)
PARTITION BY RANGE_BUCKET(date_key, GENERATE_ARRAY(20200101, 20301231, 10000))
CLUSTER BY campaign_key;

-- ------------------------------------------------------------
-- PIPELINE_RUN_LOG: Audit table for every ETL run
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `retailco.warehouse.pipeline_run_log` (
    run_id                STRING  NOT NULL,
    run_date              DATE    NOT NULL,
    source_system         STRING  NOT NULL,
    records_extracted     INT64,
    records_loaded        INT64,
    records_quarantined   INT64,
    status                STRING  NOT NULL,   -- 'SUCCESS','FAILED','PARTIAL'
    error_message         STRING,
    started_at            TIMESTAMP NOT NULL,
    completed_at          TIMESTAMP,
    duration_seconds      INT64
);

-- ------------------------------------------------------------
-- DATA_QUALITY_QUARANTINE: Failed records for investigation
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `retailco.warehouse.data_quality_quarantine` (
    quarantine_id         STRING  NOT NULL,
    run_id                STRING  NOT NULL,
    source_system         STRING  NOT NULL,
    record_raw            STRING  NOT NULL,   -- JSON string of original record
    failure_reason        STRING  NOT NULL,   -- e.g. 'NULL_PRIMARY_KEY'
    failed_check          STRING  NOT NULL,   -- e.g. 'null_check:order_id'
    quarantined_at        TIMESTAMP NOT NULL
);
