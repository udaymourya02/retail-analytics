# User Stories
## Enterprise Retail Analytics & Customer Intelligence Platform

---

| Field | Detail |
|---|---|
| **Version** | v1.0 |
| **Date** | June 2025 |
| **Author** | Uday Mourya, Analytics Engineer |
| **Format** | As a [persona], I want to [action], so that [business value] |

---

## Personas

| Persona | Role | Primary Goal |
|---|---|---|
| **Emma** | Chief Financial Officer | Monitor revenue, margin, and costs in real time |
| **James** | Head of Marketing | Understand which campaigns drive revenue |
| **Priya** | Supply Chain Manager | Prevent stockouts and overstock situations |
| **Tom** | Store Manager | See how his store is performing vs targets |
| **Lisa** | Data Analyst | Access clean, trusted data for ad hoc analysis |
| **Dev** | Data Engineer | Build and maintain reliable pipelines |

---

## Epic 1: Data Ingestion & Pipeline

### US-01
**As a** Data Engineer (Dev),  
**I want to** extract sales data from the POS REST API on an hourly schedule,  
**So that** dashboards reflect near-real-time sales performance.

**Acceptance Criteria:**
- [ ] API authentication via OAuth 2.0 token refresh
- [ ] Extraction runs every 60 minutes via GitHub Actions
- [ ] Failed runs trigger a Slack alert within 5 minutes
- [ ] Each run logs: records extracted, start time, end time, status
- [ ] Retry logic handles rate limits (max 3 retries, exponential backoff)

**Story Points:** 5 | **Priority:** Must Have

---

### US-02
**As a** Data Engineer (Dev),  
**I want to** validate all incoming data before it is loaded to the warehouse,  
**So that** bad data never reaches dashboards or analytics models.

**Acceptance Criteria:**
- [ ] Null checks on all primary key fields
- [ ] Range checks on revenue and quantity fields
- [ ] Referential integrity checks between orders and customer/product tables
- [ ] Records failing validation are quarantined and logged, not silently dropped
- [ ] Data quality report generated per pipeline run

**Story Points:** 8 | **Priority:** Must Have

---

### US-03
**As a** Data Engineer (Dev),  
**I want to** run dbt models automatically after each pipeline load,  
**So that** the analytics layer is always up to date without manual intervention.

**Acceptance Criteria:**
- [ ] GitHub Actions workflow triggers dbt run after successful ETL load
- [ ] dbt test suite runs after every model run
- [ ] Failed tests block downstream mart models from updating
- [ ] Run results are logged and accessible

**Story Points:** 5 | **Priority:** Must Have

---

## Epic 2: Executive Reporting

### US-04
**As a** CFO (Emma),  
**I want to** see total revenue, margin, and order volume on a single dashboard,  
**So that** I can assess business performance in under 2 minutes every morning.

**Acceptance Criteria:**
- [ ] Dashboard shows: Revenue, Gross Margin %, Total Orders, AOV
- [ ] All KPIs show comparison vs prior week and prior year
- [ ] Data is no older than 24 hours when I open the dashboard
- [ ] Accessible via browser on desktop and tablet — no software install required
- [ ] Loads in under 5 seconds

**Story Points:** 8 | **Priority:** Must Have

---

### US-05
**As a** CFO (Emma),  
**I want to** drill down from total revenue to store-level and product-level detail,  
**So that** I can identify which stores or products are driving or dragging performance.

**Acceptance Criteria:**
- [ ] Clicking any KPI card reveals store-level breakdown
- [ ] Store heatmap shows regional performance on a UK map
- [ ] Top 10 / Bottom 10 products by revenue visible in one click
- [ ] All drill-downs filterable by date range, category, and channel

**Story Points:** 5 | **Priority:** Must Have

---

### US-06
**As a** Store Manager (Tom),  
**I want to** see only my store's performance without seeing other stores' data,  
**So that** I can focus on what I'm responsible for.

**Acceptance Criteria:**
- [ ] Row-level security applied — Tom sees Store 14 data only
- [ ] Dashboard shows: today's revenue vs target, units sold, top products
- [ ] Week-to-date and month-to-date totals visible
- [ ] Mobile-friendly layout

**Story Points:** 5 | **Priority:** Should Have

---

## Epic 3: Customer Intelligence

### US-07
**As a** Head of Marketing (James),  
**I want to** see customers grouped into RFM segments,  
**So that** I can target the right message to the right customer group.

**Acceptance Criteria:**
- [ ] RFM segments visible in dashboard with count and % of customer base
- [ ] Segments include: Champions, Loyal, At Risk, Lost, New, Potential Loyalists
- [ ] Segment sizes updated weekly
- [ ] Ability to export segment member list (customer IDs) as CSV for CRM upload

**Story Points:** 8 | **Priority:** Must Have

---

### US-08
**As a** Head of Marketing (James),  
**I want to** see which customers have moved from Loyal to At Risk this month,  
**So that** I can trigger a win-back campaign before they churn.

**Acceptance Criteria:**
- [ ] Month-on-month segment migration matrix visible (from segment → to segment)
- [ ] At Risk segment shows: customer count, average days since last purchase, average LTV
- [ ] One-click export of At Risk customer list
- [ ] Historical segment membership stored so trends can be analysed

**Story Points:** 5 | **Priority:** Must Have

---

### US-09
**As a** Data Analyst (Lisa),  
**I want to** query RFM scores and customer lifetime value at individual customer level,  
**So that** I can build custom analysis and answer ad hoc questions from the business.

**Acceptance Criteria:**
- [ ] `mart_customer_rfm` table available in BigQuery with all RFM fields
- [ ] Table includes: customer_id, R score, F score, M score, RFM segment, CLV, segment_updated_at
- [ ] Documentation available in dbt model YAML
- [ ] Table query returns results in under 3 seconds for full customer base

**Story Points:** 3 | **Priority:** Must Have

---

## Epic 4: Inventory & Supply Chain

### US-10
**As a** Supply Chain Manager (Priya),  
**I want to** see which products are at risk of running out of stock in the next 7 days,  
**So that** I can place reorder requests before a stockout happens.

**Acceptance Criteria:**
- [ ] Inventory dashboard shows stock on hand vs reorder point per SKU
- [ ] RAG status: Red = stock below reorder point, Amber = within 20% of reorder, Green = healthy
- [ ] Filter by category, supplier, and store
- [ ] Forecasted demand for next 7 days shown alongside current stock level
- [ ] Alert email sent daily to supply chain team listing all Red-status SKUs

**Story Points:** 8 | **Priority:** Must Have

---

### US-11
**As a** Supply Chain Manager (Priya),  
**I want to** see a 12-week demand forecast per product category,  
**So that** I can plan purchasing and stock allocation in advance.

**Acceptance Criteria:**
- [ ] Forecast chart shows predicted weekly sales with 80% confidence interval
- [ ] Seasonality effects visible (e.g. Christmas uplift)
- [ ] Forecast vs actual comparison available for prior periods to assess accuracy
- [ ] MAPE metric displayed per category
- [ ] Forecast refreshed weekly every Monday morning

**Story Points:** 13 | **Priority:** Must Have

---

## Epic 5: Marketing Attribution

### US-12
**As a** Head of Marketing (James),  
**I want to** see how much revenue each marketing channel contributed last month,  
**So that** I can allocate next month's budget to the highest-performing channels.

**Acceptance Criteria:**
- [ ] Attribution model credits all touchpoints in 30-day pre-purchase window
- [ ] Dashboard shows: channel, attributed revenue, attributed orders, spend, ROAS
- [ ] Channels covered: Paid Search, Paid Social, Email, Organic, Direct
- [ ] Ability to compare attribution models: last-click vs data-driven
- [ ] Data available at campaign and ad-set level for Paid channels

**Story Points:** 13 | **Priority:** Must Have

---

### US-13
**As a** Head of Marketing (James),  
**I want to** see which customer segments respond best to which marketing channels,  
**So that** I can personalise channel strategy per segment.

**Acceptance Criteria:**
- [ ] Cross-tabulation of RFM segment vs acquisition/conversion channel
- [ ] Champions segment: which channel drove their first and most recent purchase
- [ ] At Risk segment: last channel interaction before drop-off
- [ ] Exportable for use in campaign planning

**Story Points:** 8 | **Priority:** Should Have

---

## Epic 6: Data Quality & Governance

### US-14
**As a** Data Analyst (Lisa),  
**I want to** know when a pipeline has failed or produced bad data,  
**So that** I don't unknowingly use incorrect data in my analysis.

**Acceptance Criteria:**
- [ ] Data quality dashboard shows: pipeline run status, records processed, tests passed/failed
- [ ] Email alert sent to data team within 10 minutes of any pipeline failure
- [ ] Each table shows a "data freshness" indicator — time since last successful load
- [ ] Quarantined records visible and queryable

**Story Points:** 5 | **Priority:** Must Have

---

### US-15
**As a** Data Engineer (Dev),  
**I want to** have all pipeline code version-controlled and tested via CI/CD,  
**So that** changes are safe, reviewed, and don't break production.

**Acceptance Criteria:**
- [ ] All code in GitHub repository with branch protection on main
- [ ] Pull requests require at least 1 reviewer approval before merge
- [ ] GitHub Actions runs: linting, unit tests, and dbt tests on every PR
- [ ] Failed CI checks block merge to main
- [ ] Deployment to production only from main branch via automated workflow

**Story Points:** 5 | **Priority:** Must Have

---

## Product Backlog Summary

| Epic | Stories | Total Points | Priority |
|---|---|---|---|
| Data Ingestion & Pipeline | US-01 to US-03 | 18 | Must Have |
| Executive Reporting | US-04 to US-06 | 18 | Must Have / Should Have |
| Customer Intelligence | US-07 to US-09 | 16 | Must Have |
| Inventory & Supply Chain | US-10 to US-11 | 21 | Must Have |
| Marketing Attribution | US-12 to US-13 | 21 | Must Have / Should Have |
| Data Quality & Governance | US-14 to US-15 | 10 | Must Have |
| **Total** | **15 Stories** | **104 Points** | |

---

## Sprint Plan (3 Sprints of 2 Weeks Each)

### Sprint 1 — Foundation (Weeks 1–2)
US-01, US-02, US-03, US-15
*Goal: Reliable pipeline running end-to-end with CI/CD*

### Sprint 2 — Analytics Core (Weeks 3–4)
US-04, US-05, US-07, US-09, US-10, US-14
*Goal: Core dashboards live for executive and supply chain users*

### Sprint 3 — Intelligence Layer (Weeks 5–6)
US-06, US-08, US-11, US-12, US-13
*Goal: Customer segmentation, forecasting, and attribution complete*
