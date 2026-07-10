# Functional Requirements Document (FRD)
## Enterprise Retail Analytics & Customer Intelligence Platform

---

| Field | Detail |
|---|---|
| **Document Version** | v1.0 |
| **Date** | June 2025 |
| **Author** | Uday Mourya, Analytics Engineer |
| **Status** | Approved |
| **References** | BRD v1.0 |

---

## 1. Purpose

This document translates the business requirements defined in the BRD into detailed functional specifications. It defines exactly what the system must do — the inputs, processes, outputs, and rules for each feature of the platform.

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                         │
│  POS System │ Salesforce CRM │ Marketing APIs │ WMS │ ERP  │
└──────────────────────┬──────────────────────────────────────┘
                       │ Extract
┌──────────────────────▼──────────────────────────────────────┐
│                     ETL PIPELINE (Python)                    │
│         Extract → Validate → Transform → Load               │
└──────────────────────┬──────────────────────────────────────┘
                       │ Load
┌──────────────────────▼──────────────────────────────────────┐
│              BIGQUERY DATA WAREHOUSE                         │
│    Raw Layer → Staging Layer → Marts Layer (Star Schema)    │
└──────────────────────┬──────────────────────────────────────┘
                       │ Query
┌──────────────────────▼──────────────────────────────────────┐
│              ANALYTICS & REPORTING LAYER                     │
│       dbt Models │ Python Analytics │ BI Dashboards         │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Data Ingestion — Functional Requirements

### 3.1 Source Systems

| Source | Connection Method | Frequency | Format |
|---|---|---|---|
| POS System | REST API | Every 1 hour | JSON |
| Salesforce CRM | Salesforce REST API | Daily at 02:00 | JSON |
| Google Ads | Google Ads API | Daily at 03:00 | JSON |
| Meta Ads | Meta Marketing API | Daily at 03:00 | JSON |
| Warehouse WMS | SFTP file transfer | Daily at 01:00 | CSV |
| Finance ERP | Database direct connection | Daily at 04:00 | SQL query |

### 3.2 Extraction Rules

**FR-01:** The extractor must authenticate using OAuth 2.0 for all API sources. Credentials must be stored in environment variables, never hardcoded.

**FR-02:** Each extraction run must log: source system, records extracted, extraction start time, extraction end time, and status (success/failure).

**FR-03:** The system must handle API rate limits by implementing exponential backoff retry logic (max 3 retries, 30-second intervals).

**FR-04:** If any source system is unavailable, the pipeline must continue extracting from all other sources and raise an alert for the failed source only.

---

## 4. Data Transformation — Functional Requirements

### 4.1 Data Cleaning Rules

**FR-05:** Null values must be handled as follows:
- Numeric fields: fill with 0 or column mean (context-dependent, documented per field)
- String fields: fill with "UNKNOWN"
- Date fields: flag as `date_missing = TRUE`, exclude from time-based calculations

**FR-06:** Duplicate records must be identified by a composite key (source_system + record_id + timestamp) and deduplicated, retaining the most recent record.

**FR-07:** All date/time fields must be standardised to UTC ISO 8601 format: `YYYY-MM-DD HH:MM:SS`.

**FR-08:** Currency fields must be stored in pence (integer) to avoid floating point errors. Display layer converts to pounds.

### 4.2 Data Validation Rules

**FR-09:** The following checks must pass before any data is loaded to the warehouse:

| Check | Rule | Action on Failure |
|---|---|---|
| Null check | Primary key fields must not be null | Reject record, log error |
| Range check | Order value must be > 0 and < £50,000 | Flag for review |
| Referential integrity | Customer ID in orders must exist in customer table | Reject record |
| Freshness check | Source data must be no older than 26 hours | Alert data team |
| Volume check | Record count must be within 20% of 7-day average | Alert data team |

---

## 5. Data Warehouse — Functional Requirements

### 5.1 Star Schema Design

The warehouse must implement a star schema with the following tables:

**Fact Tables:**
- `fact_sales` — one row per order line item
- `fact_inventory` — one row per product per store per day
- `fact_marketing_spend` — one row per campaign per day

**Dimension Tables:**
- `dim_customer` — one row per customer
- `dim_product` — one row per product (SKU)
- `dim_store` — one row per store location
- `dim_date` — one row per calendar date (pre-populated 2020–2030)
- `dim_channel` — one row per sales channel (in-store, online, app)
- `dim_campaign` — one row per marketing campaign

**FR-10:** All fact tables must include a surrogate key, all relevant foreign keys to dimension tables, and audit columns: `created_at`, `updated_at`, `pipeline_run_id`.

**FR-11:** The `dim_date` table must include: date, day of week, week number, month, quarter, year, is_weekend, is_public_holiday, is_promotional_period.

**FR-12:** Slowly Changing Dimensions (SCD Type 2) must be implemented for `dim_customer` and `dim_product` to track historical changes.

### 5.2 dbt Model Layers

**FR-13:** All SQL transformations must be implemented as dbt models following this three-layer structure:

| Layer | Prefix | Purpose |
|---|---|---|
| Staging | `stg_` | 1:1 with source, rename columns, cast types only |
| Intermediate | `int_` | Join staging models, apply business logic |
| Marts | `mart_` | Final analytics-ready tables, one per business domain |

**FR-14:** Every dbt model must have a corresponding schema.yml entry with description, column descriptions, and at least `not_null` and `unique` tests on primary keys.

---

## 6. Analytics Features — Functional Requirements

### 6.1 RFM Customer Segmentation

**FR-15:** The RFM model must calculate the following per customer, based on the last 12 months of transactions:

| Metric | Definition |
|---|---|
| Recency (R) | Days since most recent purchase |
| Frequency (F) | Total number of distinct purchase dates |
| Monetary (M) | Total net revenue (excl. returns and VAT) |

**FR-16:** Each R, F, and M metric must be scored 1–5 using quintile ranking (5 = best).

**FR-17:** Customers must be assigned to one of the following segments based on RFM scores:

| Segment | RFM Rule |
|---|---|
| Champions | R=5, F≥4, M≥4 |
| Loyal Customers | F≥3, M≥3 |
| At Risk | R≤2, F≥3 |
| Lost | R=1, F≤2 |
| New Customers | F=1, R≥4 |
| Potential Loyalists | R≥4, F=2 |

**FR-18:** RFM segmentation must be recalculated weekly and stored with a run date for trend analysis.

### 6.2 Demand Forecasting

**FR-19:** Sales forecasting must use the Facebook Prophet model with the following configuration:
- Forecast horizon: 12 weeks ahead
- Seasonality: weekly + annual
- Holiday effects: UK public holidays must be included as regressors
- Uncertainty interval: 80% confidence interval must be stored

**FR-20:** Forecasts must be generated at product-category level (not SKU level) to ensure statistical stability.

**FR-21:** Forecast accuracy must be evaluated using MAPE (Mean Absolute Percentage Error). Target: MAPE ≤ 15%.

### 6.3 Marketing Attribution

**FR-22:** The platform must implement a data-driven multi-touch attribution model assigning credit to marketing touchpoints in the 30-day window before a purchase.

**FR-23:** Attribution must be calculated for the following channels: Paid Search (Google), Paid Social (Meta), Email, Organic Search, Direct.

**FR-24:** The output must include: channel, attributed revenue, attributed orders, cost per attributed order, and ROAS (Return on Ad Spend).

---

## 7. Dashboard Requirements

### 7.1 Executive KPI Dashboard (Power BI)

**FR-25:** Must display the following KPIs with period-on-period comparison (vs prior week and prior year):
- Total Revenue
- Total Orders
- Average Order Value (AOV)
- Gross Margin %
- New vs Returning Customer split
- Top 10 products by revenue

**FR-26:** Must include a store performance heatmap showing revenue by region.

**FR-27:** Must be filterable by: date range, store, product category, and sales channel.

### 7.2 Customer Intelligence Dashboard

**FR-28:** Must display RFM segment distribution (count and % of customer base).

**FR-29:** Must show segment migration — how customers have moved between segments month-on-month.

**FR-30:** Must highlight top 100 customers by CLV with drill-through to individual customer profile.

### 7.3 Inventory Dashboard

**FR-31:** Must show current stock levels vs reorder point for all SKUs, with RAG (Red/Amber/Green) status.

**FR-32:** Must display forecasted demand vs current stock to identify forward-looking stockout risk.

---

## 8. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-01 | Performance | Dashboard queries must return results in under 5 seconds |
| NFR-02 | Availability | Pipeline must achieve 99.5% uptime SLA |
| NFR-03 | Security | All data in transit must be encrypted (TLS 1.2+) |
| NFR-04 | Security | All data at rest must be encrypted (AES-256) |
| NFR-05 | Compliance | Customer PII (name, email, address) must be masked in analytics layer |
| NFR-06 | Scalability | Architecture must support 10x data volume growth without redesign |
| NFR-07 | Auditability | All pipeline runs must be logged with full audit trail |

---

## 9. Data Dictionary (Key Fields)

| Field | Table | Type | Description |
|---|---|---|---|
| `order_id` | fact_sales | STRING | Unique identifier for each order |
| `customer_id` | fact_sales, dim_customer | STRING | Unique identifier for each customer |
| `product_id` | fact_sales, dim_product | STRING | SKU-level product identifier |
| `store_id` | fact_sales, dim_store | STRING | Store identifier |
| `order_date_key` | fact_sales | INTEGER | Foreign key to dim_date (YYYYMMDD) |
| `net_revenue_pence` | fact_sales | INTEGER | Revenue after discounts, excl. VAT, in pence |
| `units_sold` | fact_sales | INTEGER | Quantity of product sold in this line item |
| `rfm_segment` | dim_customer | STRING | Current RFM segment label |
| `stock_on_hand` | fact_inventory | INTEGER | Units in stock at end of day |
| `reorder_point` | fact_inventory | INTEGER | Units threshold that triggers reorder |
