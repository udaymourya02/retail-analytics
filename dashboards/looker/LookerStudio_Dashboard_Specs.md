# Looker Studio Dashboard Specifications
## Enterprise Retail Analytics & Customer Intelligence Platform

---

| Field | Detail |
|---|---|
| **Tool** | Google Looker Studio (free) |
| **Data Source** | Google BigQuery — `retailco.warehouse` dataset |
| **Author** | Uday Mourya |
| **Dashboards** | 4 reports (one per business domain) |

---

## Why Looker Studio

- 100% free — no licence required
- Connects natively to BigQuery (same GCP project)
- Shareable via URL — no software install for viewers
- Professional enough for portfolio and employer demos
- Can embed in websites and presentations

---

## Setup: Connect BigQuery to Looker Studio

1. Go to **lookerstudio.google.com** → Create → Report
2. Select **BigQuery** as data source
3. Choose your GCP project → dataset `warehouse` → select a mart table
4. Repeat for each mart table needed in the report
5. Use **Blend Data** to join multiple sources within one chart

---

## Dashboard 1: Executive KPI Dashboard

**Data Source:** `mart_executive_kpis`
**Audience:** CEO, CFO
**Refresh:** Daily

### Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  RETAILCO — EXECUTIVE DASHBOARD          [Date filter: MTD ▼]  │
├──────────┬──────────┬──────────┬──────────┬────────────────────┤
│ REVENUE  │  ORDERS  │   AOV    │  MARGIN  │  YoY GROWTH        │
│ £2.4M    │  18,240  │ £131.60  │  42.3%   │  +8.4%             │
│ ▲ +6.2%  │ ▲ +4.1%  │ ▲ +1.9%  │ ▲ +0.8%  │                    │
│ vs LW    │ vs LW    │ vs LW    │ vs LW    │                    │
├──────────┴──────────┴──────────┴──────────┴────────────────────┤
│                                                                 │
│  Revenue Trend (last 90 days)          New vs Returning        │
│  [Line chart — daily revenue]          [Donut chart]           │
│                                                                 │
├──────────────────────────────────┬──────────────────────────────┤
│  Revenue by Region (UK map)      │  Top 10 Products (bar chart) │
│  [Geo chart — filled UK map]     │  [Horizontal bar]            │
│                                  │                              │
├──────────────────────────────────┴──────────────────────────────┤
│  Store Performance Table                                        │
│  [Table: Store | Revenue | Orders | AOV | Margin | WoW %]      │
└─────────────────────────────────────────────────────────────────┘
```

### Charts Specification

| Chart | Type | Dimension | Metric | Filter |
|---|---|---|---|---|
| Revenue KPI card | Scorecard | — | SUM(revenue_gbp) | Date range |
| WoW comparison | Scorecard | — | revenue_growth_wow_pct | — |
| Revenue trend | Time series | order_date | revenue_gbp | — |
| New vs Returning | Donut | — | new / returning ratio | — |
| UK Map | Geo chart | store_region | revenue_gbp | — |
| Top 10 Products | Bar (horiz) | product_name | revenue_gbp | Top 10 filter |
| Store table | Table | store_name | revenue_gbp, orders, aov | Sortable |

### Filters to Add
- Date range control (default: current month)
- Store dropdown
- Category dropdown
- Channel toggle (Online / In-Store)

---

## Dashboard 2: Customer Intelligence Dashboard

**Data Sources:** `mart_customer_rfm`
**Audience:** Head of Marketing
**Refresh:** Weekly (Monday)

### Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  CUSTOMER INTELLIGENCE             [Segment filter ▼]          │
├──────────────────────────┬──────────────────────────────────────┤
│ TOTAL CUSTOMERS          │  CHAMPIONS      AT RISK              │
│ 5,000                    │  675 (13.5%)    861 (17.2%)          │
│                          │  £8,393 avg LTV £7,720 avg LTV       │
├──────────────────────────┴──────────────────────────────────────┤
│  Segment Distribution                  Revenue by Segment       │
│  [Horizontal bar chart]                [Pie / donut chart]      │
│  Champions     ██████░░░░ 675         Champions  £5.7M (17%)   │
│  Loyal         ████████░░ 950         Loyal      £7.0M (21%)   │
│  At Risk       ███████░░░ 861         At Risk    £6.6M (20%)   │
│  New           ██████░░░░ 679         ...                      │
├──────────────────────────────────────────────────────────────────┤
│  RFM Heatmap (R score vs F score, colour = avg revenue)         │
│  [Pivot table with conditional formatting]                      │
├──────────────────────────────────────────────────────────────────┤
│  Customer Table (Top 100 by LTV)                                │
│  [Table: Customer ID | Segment | LTV | Orders | Last Purchase]  │
│  [Export button for CRM upload]                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Charts Specification

| Chart | Type | Dimension | Metric |
|---|---|---|---|
| Segment bar | Horizontal bar | rfm_segment | COUNT(customer_id) |
| Revenue donut | Donut | rfm_segment | SUM(total_revenue_gbp) |
| LTV scorecard | Scorecard | — | AVG(total_revenue_gbp) |
| RFM heatmap | Pivot table | r_score × f_score | AVG(total_revenue_gbp) |
| Customer table | Table | customer_id, rfm_segment | total_revenue_gbp, total_orders, last_purchase_date |

### Conditional Formatting on Segment column
- Champions → green background
- Loyal Customers → light green
- At Risk → orange
- Lost → red

---

## Dashboard 3: Inventory Dashboard

**Data Sources:** `mart_inventory_status`
**Audience:** Supply Chain Manager
**Refresh:** Daily (post-ETL)

### Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  INVENTORY DASHBOARD         [Category ▼] [Store ▼]           │
├──────────┬──────────┬──────────────────────────────────────────┤
│ RED SKUs │ AMBER    │ TOTAL SKUS     POTENTIAL LOST REVENUE     │
│    47    │   128    │    2,000            £84,200               │
│ (Reorder │(Monitor) │                                          │
│  needed) │          │                                          │
├──────────┴──────────┴──────────────────────────────────────────┤
│  Stock Status Summary          Days of Stock Remaining         │
│  [Stacked bar by category]     [Histogram]                     │
│  GREEN █████ 82%                                               │
│  AMBER ███   12%                                               │
│  RED   █     6%                                                │
├─────────────────────────────────────────────────────────────────┤
│  Critical Stock Table (RED items)                               │
│  [Table sorted by days_of_stock_remaining ASC]                  │
│  Product | Category | Store | Stock | Reorder Pt | Days Left   │
│  [Row colour = RED for stock=0, AMBER for near reorder]        │
└─────────────────────────────────────────────────────────────────┘
```

### Charts Specification

| Chart | Type | Dimension | Metric |
|---|---|---|---|
| RED count scorecard | Scorecard | — | COUNTIF(stock_status="RED") |
| Status stacked bar | Bar | category | COUNT by stock_status |
| Days of stock hist | Histogram | — | days_of_stock_remaining |
| Critical table | Table | product_name, store_name | stock_on_hand, reorder_point, days_of_stock_remaining |
| Lost revenue card | Scorecard | — | SUM(potential_lost_revenue_gbp) |

---

## Dashboard 4: Marketing Attribution Dashboard

**Data Sources:** `mart_marketing_attribution`
**Audience:** Head of Marketing
**Refresh:** Monthly (first Monday)

### Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  MARKETING ATTRIBUTION          [Month ▼] [Channel ▼]         │
├──────────┬──────────┬──────────┬────────────────────────────────┤
│  SPEND   │ ATT.REV  │   ROAS   │  COST/ORDER                   │
│  £48,200 │ £241,000 │   5.0x   │  £12.40                       │
├──────────┴──────────┴──────────┴────────────────────────────────┤
│  Revenue by Channel                ROAS by Channel              │
│  [Horizontal bar]                  [Bar chart]                  │
│  Paid Search   ████████  £95K      Paid Search    4.8x         │
│  Email         ██████    £72K      Email          9.2x         │
│  Paid Social   █████     £48K      Organic        ∞            │
│  Organic       ████      £26K      Paid Social    3.1x         │
├─────────────────────────────────────────────────────────────────┤
│  Spend vs Revenue Scatter (one dot per campaign)               │
│  [Scatter plot: x=spend, y=attributed_revenue, size=orders]    │
├─────────────────────────────────────────────────────────────────┤
│  Campaign Detail Table                                         │
│  Campaign | Channel | Spend | Revenue | Orders | ROAS | CTR%  │
└─────────────────────────────────────────────────────────────────┘
```

---

## How to Build Each Chart (Step by Step)

### Adding a Scorecard (KPI card)
1. Insert → Scorecard
2. Set **Metric** = e.g. `SUM(revenue_gbp)`
3. Add **Comparison metric** = `revenue_growth_wow_pct`
4. Format: Currency, 0 decimal places
5. Style: Large font, white text on dark background

### Adding a Time Series (revenue trend)
1. Insert → Time series chart
2. **Dimension** = `order_date`
3. **Metric** = `SUM(revenue_gbp)`
4. Date range granularity = Day
5. Enable **Smooth** and **Comparison line** (prior period)

### Adding a Geo Map (UK stores)
1. Insert → Geo chart
2. **Geo dimension** = `store_region`
3. **Metric** = `SUM(revenue_gbp)`
4. Zoom area = United Kingdom
5. Colour range: white → dark blue

### Conditional Formatting on Tables
1. Click table → Style tab
2. Add **Conditional formatting rule**
3. Field = `stock_status`, Value = "RED", Background = #E74C3C

### Blending Data Sources (joining two marts)
1. Resource → Manage blended data
2. Add data source 1 (e.g. mart_customer_rfm)
3. Add data source 2 (e.g. mart_executive_kpis)
4. Set join key (e.g. customer_id or date)
5. Choose join type (Left join recommended)

---

## Portfolio Tips

1. **Screenshot every dashboard** — add to GitHub under `dashboards/looker/screenshots/`
2. **Record a 2-min Loom walkthrough** — link it in your README
3. **Share a view-only Looker Studio link** — paste into your LinkedIn and CV
4. On your CV write: *"Built 4 Looker Studio dashboards connected to BigQuery (mart layer)"*
5. In interviews: *"I chose Looker Studio because it integrates natively with our BigQuery data warehouse on GCP, giving sub-5-second query times without additional infrastructure"*
