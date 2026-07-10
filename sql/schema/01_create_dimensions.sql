-- ============================================================
-- DIMENSION TABLES — RetailCo Analytics Platform
-- Target: Google BigQuery
-- Author: Uday Mourya
-- ============================================================

-- ------------------------------------------------------------
-- DIM_DATE: Calendar dimension (pre-populated 2020–2030)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `retailco.warehouse.dim_date` (
    date_key          INT64   NOT NULL,   -- YYYYMMDD surrogate key
    full_date         DATE    NOT NULL,
    day_of_week       STRING  NOT NULL,   -- 'Monday', 'Tuesday' etc.
    day_of_week_num   INT64   NOT NULL,   -- 1=Monday ... 7=Sunday
    week_number       INT64   NOT NULL,
    month_num         INT64   NOT NULL,
    month_name        STRING  NOT NULL,
    quarter           INT64   NOT NULL,
    year              INT64   NOT NULL,
    is_weekend        BOOL    NOT NULL,
    is_uk_public_holiday BOOL NOT NULL,
    holiday_name      STRING,             -- NULL if not a holiday
    is_promotional    BOOL    NOT NULL DEFAULT FALSE,
    season            STRING  NOT NULL    -- 'Spring','Summer','Autumn','Winter'
);

-- ------------------------------------------------------------
-- DIM_STORE: One row per physical store or online channel
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `retailco.warehouse.dim_store` (
    store_key         INT64   NOT NULL,
    store_id          STRING  NOT NULL,   -- natural key e.g. 'STR-014'
    store_name        STRING  NOT NULL,
    store_type        STRING  NOT NULL,   -- 'Physical', 'Online', 'App'
    city              STRING,
    region            STRING,             -- 'London','North West' etc.
    country           STRING  NOT NULL DEFAULT 'United Kingdom',
    postcode          STRING,
    opening_date      DATE,
    is_active         BOOL    NOT NULL DEFAULT TRUE,
    -- SCD Type 2 columns
    valid_from        DATE    NOT NULL,
    valid_to          DATE,               -- NULL = current record
    is_current        BOOL    NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMP NOT NULL,
    updated_at        TIMESTAMP NOT NULL
);

-- ------------------------------------------------------------
-- DIM_CUSTOMER: One row per customer (SCD Type 2)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `retailco.warehouse.dim_customer` (
    customer_key      INT64   NOT NULL,
    customer_id       STRING  NOT NULL,   -- natural key from CRM
    -- PII masked in analytics layer
    email_masked      STRING,             -- e.g. j***@gmail.com
    age_band          STRING,             -- '18-24','25-34' etc.
    gender            STRING,
    city              STRING,
    region            STRING,
    postcode_district STRING,             -- e.g. 'SW1' (not full postcode)
    acquisition_channel STRING,           -- first channel that brought customer
    acquisition_date  DATE,
    loyalty_tier      STRING,             -- 'Bronze','Silver','Gold','Platinum'
    -- RFM fields (updated weekly)
    rfm_recency_score INT64,
    rfm_frequency_score INT64,
    rfm_monetary_score INT64,
    rfm_segment       STRING,
    rfm_updated_at    TIMESTAMP,
    -- Lifetime value
    customer_ltv_gbp  FLOAT64,
    -- SCD Type 2 columns
    valid_from        DATE    NOT NULL,
    valid_to          DATE,
    is_current        BOOL    NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMP NOT NULL,
    updated_at        TIMESTAMP NOT NULL
);

-- ------------------------------------------------------------
-- DIM_PRODUCT: One row per SKU (SCD Type 2)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `retailco.warehouse.dim_product` (
    product_key       INT64   NOT NULL,
    product_id        STRING  NOT NULL,   -- SKU
    product_name      STRING  NOT NULL,
    category          STRING  NOT NULL,   -- 'Womenswear','Menswear','Accessories'
    subcategory       STRING,
    brand             STRING,
    supplier_id       STRING,
    supplier_name     STRING,
    cost_price_pence  INT64,              -- pence to avoid float errors
    rrp_pence         INT64,              -- recommended retail price
    is_active         BOOL    NOT NULL DEFAULT TRUE,
    launch_date       DATE,
    discontinue_date  DATE,
    -- SCD Type 2 columns
    valid_from        DATE    NOT NULL,
    valid_to          DATE,
    is_current        BOOL    NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMP NOT NULL,
    updated_at        TIMESTAMP NOT NULL
);

-- ------------------------------------------------------------
-- DIM_CHANNEL: Sales channels
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `retailco.warehouse.dim_channel` (
    channel_key       INT64   NOT NULL,
    channel_id        STRING  NOT NULL,
    channel_name      STRING  NOT NULL,   -- 'In-Store','Online','App','Wholesale'
    channel_type      STRING  NOT NULL,   -- 'Physical','Digital'
    created_at        TIMESTAMP NOT NULL
);

-- ------------------------------------------------------------
-- DIM_CAMPAIGN: Marketing campaigns
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `retailco.warehouse.dim_campaign` (
    campaign_key      INT64   NOT NULL,
    campaign_id       STRING  NOT NULL,
    campaign_name     STRING  NOT NULL,
    channel           STRING  NOT NULL,   -- 'Paid Search','Paid Social','Email'
    start_date        DATE,
    end_date          DATE,
    budget_pence      INT64,
    objective         STRING,             -- 'Awareness','Conversion','Retention'
    created_at        TIMESTAMP NOT NULL,
    updated_at        TIMESTAMP NOT NULL
);
