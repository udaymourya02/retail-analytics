# BPMN Process Flow Diagrams
## Enterprise Retail Analytics & Customer Intelligence Platform

---

| Field | Detail |
|---|---|
| **Version** | v1.0 |
| **Date** | June 2025 |
| **Author** | Uday Mourya, Analytics Engineer |
| **Tool** | Diagrams created in draw.io / Lucidchart (see /docs/diagrams/*.drawio) |

---

## Process 1: Daily ETL Pipeline

**Process Name:** Daily Data Ingestion and Loading  
**Trigger:** Scheduled — 01:00 UTC daily (GitHub Actions cron)  
**Actors:** GitHub Actions (Orchestrator), Python ETL, BigQuery, Alerting System

```
┌─────────────────────────────────────────────────────────────────────┐
│ START EVENT: GitHub Actions cron trigger (01:00 UTC)                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Parallel Gateway │ (fork — all sources run in parallel)
                    └──┬──────┬───┬───┘
             ┌─────────┘      │   └──────────┐
             ▼                ▼              ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Extract POS  │  │ Extract CRM  │  │ Extract WMS  │  ... (all 5 sources)
    │ (REST API)   │  │ (Salesforce) │  │ (SFTP/CSV)   │
    └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
           │                 │                  │
           ▼                 ▼                  ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Success?     │  │ Success?     │  │ Success?     │
    └──┬───────┬───┘  └──┬───────┬───┘  └──┬───────┬───┘
       │ YES   │ NO      │ YES   │ NO      │ YES   │ NO
       │       ▼         │       ▼         │       ▼
       │  ┌─────────┐    │  ┌─────────┐   │  ┌─────────┐
       │  │  RETRY  │    │  │  RETRY  │   │  │  RETRY  │
       │  │(x3 exp) │    │  │(x3 exp) │   │  │(x3 exp) │
       │  └────┬────┘    │  └────┬────┘   │  └────┬────┘
       │  Still│fail?    │  Still│fail?   │  Still│fail?
       │       ▼         │       ▼         │       ▼
       │  ┌─────────┐    │  ┌─────────┐   │  ┌─────────┐
       │  │  ALERT  │    │  │  ALERT  │   │  │  ALERT  │
       │  │ (email) │    │  │ (email) │   │  │ (email) │
       │  └─────────┘    │  └─────────┘   │  └─────────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Join Gateway   │ (all successful extracts merge)
                    └────────┬────────┘
                             │
                    ┌────────▼────────────────┐
                    │  Data Validation Layer   │
                    │  - Null checks           │
                    │  - Range checks          │
                    │  - Referential integrity │
                    │  - Volume checks         │
                    └────────┬────────────────┘
                             │
                    ┌────────▼────────┐
                    │ Validation Pass? │
                    └──┬──────────┬───┘
                       │ YES      │ NO
                       │          ▼
                       │  ┌─────────────────┐
                       │  │ Quarantine       │
                       │  │ Failed Records   │
                       │  │ Log DQ Report    │
                       │  └─────────────────┘
                       │
              ┌────────▼──────────────────┐
              │ Load to BigQuery Raw Layer │
              └────────┬──────────────────┘
                       │
              ┌────────▼──────────────────┐
              │ Trigger dbt Run            │
              │ (staging → intermediate   │
              │  → marts)                 │
              └────────┬──────────────────┘
                       │
              ┌────────▼──────────────────┐
              │ dbt Tests Pass?            │
              └──┬──────────┬─────────────┘
                 │ YES      │ NO
                 │          ▼
                 │  ┌─────────────────────┐
                 │  │ Block Mart Update   │
                 │  │ Alert Data Team     │
                 │  └─────────────────────┘
                 │
        ┌────────▼──────────────────────┐
        │ Update Pipeline Run Log       │
        │ (status, counts, timestamps)  │
        └────────┬──────────────────────┘
                 │
        ┌────────▼────┐
        │  END EVENT  │
        └─────────────┘
```

---

## Process 2: Customer RFM Segmentation

**Process Name:** Weekly Customer Segmentation Update  
**Trigger:** Scheduled — Every Monday 06:00 UTC  
**Actors:** GitHub Actions, Python (RFM script), BigQuery, Salesforce CRM

```
┌──────────────────────────────────────────────┐
│ START: Monday 06:00 UTC trigger              │
└──────────────────┬───────────────────────────┘
                   │
          ┌────────▼────────────────────────┐
          │ Query fact_sales (last 12 months)│
          │ from BigQuery mart layer         │
          └────────┬────────────────────────┘
                   │
          ┌────────▼──────────────────────┐
          │ Calculate per customer:        │
          │  - Recency (days since last)   │
          │  - Frequency (distinct dates)  │
          │  - Monetary (net revenue)      │
          └────────┬──────────────────────┘
                   │
          ┌────────▼──────────────────────┐
          │ Score R, F, M 1–5 (quintile)  │
          └────────┬──────────────────────┘
                   │
          ┌────────▼──────────────────────┐
          │ Apply segment rules           │
          │ → Assign segment label        │
          └────────┬──────────────────────┘
                   │
          ┌────────▼──────────────────────┐
          │ Write to mart_customer_rfm    │
          │ (with run_date for history)   │
          └────────┬──────────────────────┘
                   │
          ┌────────▼──────────────────────┐
          │ Calculate segment migration   │
          │ (vs prior week)               │
          └────────┬──────────────────────┘
                   │
          ┌────────▼──────────────────────┐
          │ Customers moved to At Risk?   │
          └──┬────────────┬───────────────┘
             │ YES        │ NO
             ▼            │
    ┌──────────────────┐  │
    │ Trigger CRM      │  │
    │ export for At    │  │
    │ Risk segment     │  │
    └──────────────────┘  │
             │            │
             └─────┬──────┘
                   │
          ┌────────▼────┐
          │  END EVENT  │
          └─────────────┘
```

---

## Process 3: Inventory Alert Workflow

**Process Name:** Daily Inventory Monitoring and Alerting  
**Trigger:** Scheduled — Daily 07:00 UTC (after ETL completes)  
**Actors:** GitHub Actions, Python, BigQuery, Email System, Supply Chain Team

```
┌─────────────────────────────────────────┐
│ START: 07:00 UTC (post-ETL trigger)     │
└───────────────────┬─────────────────────┘
                    │
           ┌────────▼─────────────────────┐
           │ Query fact_inventory for      │
           │ today (all SKUs, all stores)  │
           └────────┬─────────────────────┘
                    │
           ┌────────▼─────────────────────┐
           │ Compare stock_on_hand vs      │
           │ reorder_point per SKU         │
           └────────┬─────────────────────┘
                    │
           ┌────────▼─────────────────────┐
           │ Assign RAG Status:            │
           │ RED:   stock ≤ reorder_point  │
           │ AMBER: stock ≤ 120% reorder   │
           │ GREEN: stock > 120% reorder   │
           └────────┬─────────────────────┘
                    │
           ┌────────▼─────────────────────┐
           │ Any RED status SKUs?          │
           └──┬──────────────┬────────────┘
              │ YES          │ NO
              ▼              │
    ┌──────────────────┐     │
    │ Generate alert   │     │
    │ email with RED   │     │
    │ SKU list         │     │
    │ + 7-day forecast │     │
    └──────┬───────────┘     │
           │                 │
           ▼                 │
    ┌──────────────────┐     │
    │ Send to Supply   │     │
    │ Chain team +     │     │
    │ Store Managers   │     │
    └──────┬───────────┘     │
           │                 │
           └─────┬───────────┘
                 │
        ┌────────▼──────────────────────┐
        │ Update Inventory Dashboard    │
        │ (RAG status refreshed)        │
        └────────┬──────────────────────┘
                 │
        ┌────────▼────┐
        │  END EVENT  │
        └─────────────┘
```

---

## Process 4: Marketing Attribution Report Generation

**Process Name:** Monthly Marketing Attribution Report  
**Trigger:** First Monday of each month, 08:00 UTC  
**Actors:** GitHub Actions, Python Attribution Model, BigQuery, Power BI, Marketing Team

```
┌──────────────────────────────────────────────┐
│ START: First Monday of month, 08:00 UTC      │
└──────────────────┬───────────────────────────┘
                   │
          ┌────────▼────────────────────────┐
          │ Pull marketing touchpoint data  │
          │ - Google Ads impressions/clicks │
          │ - Meta Ads interactions         │
          │ - Email opens/clicks            │
          │ For prior calendar month        │
          └────────┬────────────────────────┘
                   │
          ┌────────▼────────────────────────┐
          │ Pull conversion events          │
          │ (purchases) from fact_sales     │
          └────────┬────────────────────────┘
                   │
          ┌────────▼────────────────────────┐
          │ Build 30-day attribution        │
          │ window per customer             │
          │ (all touchpoints before purchase)│
          └────────┬────────────────────────┘
                   │
          ┌────────▼────────────────────────┐
          │ Apply multi-touch attribution   │
          │ model (data-driven weighting)   │
          └────────┬────────────────────────┘
                   │
          ┌────────▼────────────────────────┐
          │ Calculate per channel:          │
          │ - Attributed revenue            │
          │ - Attributed orders             │
          │ - ROAS                          │
          └────────┬────────────────────────┘
                   │
          ┌────────▼────────────────────────┐
          │ Write to mart_attribution       │
          └────────┬────────────────────────┘
                   │
          ┌────────▼────────────────────────┐
          │ Power BI dashboard auto-        │
          │ refreshes from mart             │
          └────────┬────────────────────────┘
                   │
          ┌────────▼────────────────────────┐
          │ Send summary email to           │
          │ Head of Marketing               │
          └────────┬────────────────────────┘
                   │
          ┌────────▼────┐
          │  END EVENT  │
          └─────────────┘
```

---

*Note: Full interactive BPMN diagrams (draw.io format) are located in `/docs/diagrams/` with `.drawio` file extension. These can be opened in draw.io (free) or Lucidchart.*
