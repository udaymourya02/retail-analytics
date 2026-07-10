# UAT Test Cases
## Enterprise Retail Analytics & Customer Intelligence Platform

---

| Field | Detail |
|---|---|
| **Version** | v1.0 |
| **Date** | July 2025 |
| **Author** | Uday Mourya, Analytics Engineer |
| **UAT Lead** | Priya Nair, Head of Data |
| **UAT Period** | Week 11–12 of project |

---

## UAT Approach

User Acceptance Testing is conducted by business stakeholders (not the development team) in a staging environment populated with production-representative data. Each test case maps to one or more User Stories. Testers sign off each test case as **Pass**, **Fail**, or **Conditional Pass** (pass with minor defects logged).

---

## Module 1: Data Pipeline & Freshness

### TC-001: Daily Pipeline Execution
**Related User Story:** US-01, US-02  
**Tester:** Data Team  
**Priority:** Critical

| Step | Action | Expected Result |
|---|---|---|
| 1 | Check GitHub Actions at 06:00 | Pipeline workflow shows green (success) status |
| 2 | Query `pipeline_run_log` table in BigQuery | Record exists for today's run with status = 'SUCCESS' |
| 3 | Check records_extracted column | Count is within 20% of 7-day average |
| 4 | Open Power BI dashboard | "Last updated" timestamp shows today's date |

**Pass Criteria:** All 4 steps pass  
**Result:** [ ] Pass [ ] Fail [ ] Conditional  
**Tester Sign-off:** _________________ **Date:** _______

---

### TC-002: Pipeline Failure Alert
**Related User Story:** US-14  
**Tester:** Data Team  
**Priority:** Critical

| Step | Action | Expected Result |
|---|---|---|
| 1 | Temporarily revoke API credentials for POS source | — |
| 2 | Wait for next scheduled pipeline run | — |
| 3 | Check email inbox | Alert email received within 10 minutes of failure |
| 4 | Check alert content | Email contains: source system name, error message, pipeline run ID, timestamp |
| 5 | Check other source systems | Pipeline continued loading all other sources successfully |
| 6 | Restore credentials | — |

**Pass Criteria:** Steps 3, 4, and 5 pass  
**Result:** [ ] Pass [ ] Fail [ ] Conditional  
**Tester Sign-off:** _________________ **Date:** _______

---

### TC-003: Data Quality Validation
**Related User Story:** US-02  
**Tester:** Lisa (Data Analyst)  
**Priority:** High

| Step | Action | Expected Result |
|---|---|---|
| 1 | Insert a test record with NULL order_id into source | — |
| 2 | Run pipeline | Record is rejected — NOT loaded to warehouse |
| 3 | Query `data_quality_quarantine` table | Rejected record present with reason = 'NULL_PRIMARY_KEY' |
| 4 | Insert a test record with order_value = -500 | — |
| 5 | Run pipeline | Record is flagged and quarantined, not silently dropped |
| 6 | Check main fact_sales table | Neither test record present in warehouse |

**Pass Criteria:** All steps pass  
**Result:** [ ] Pass [ ] Fail [ ] Conditional  
**Tester Sign-off:** _________________ **Date:** _______

---

## Module 2: Executive KPI Dashboard

### TC-004: KPI Accuracy — Revenue
**Related User Story:** US-04  
**Tester:** Emma (CFO)  
**Priority:** Critical

| Step | Action | Expected Result |
|---|---|---|
| 1 | Open Executive Dashboard in Power BI | Dashboard loads in under 5 seconds |
| 2 | Note total revenue shown for yesterday | — |
| 3 | Run verification SQL query against BigQuery | `SELECT SUM(net_revenue_pence)/100 FROM fact_sales WHERE order_date = YESTERDAY` |
| 4 | Compare dashboard figure to SQL result | Values match within £1 (rounding only) |
| 5 | Check prior week comparison % | Matches manual calculation from raw data |

**Pass Criteria:** Step 1 timing and Step 4 accuracy both pass  
**Result:** [ ] Pass [ ] Fail [ ] Conditional  
**Tester Sign-off:** _________________ **Date:** _______

---

### TC-005: Dashboard Filtering
**Related User Story:** US-04, US-05  
**Tester:** Emma (CFO)  
**Priority:** High

| Step | Action | Expected Result |
|---|---|---|
| 1 | Apply date filter: last 7 days | All KPIs update to reflect 7-day window |
| 2 | Apply store filter: London stores only | Revenue card shows only London store revenue |
| 3 | Apply category filter: Womenswear | Top products list shows only Womenswear products |
| 4 | Clear all filters | Dashboard returns to default (MTD) view |
| 5 | Select a KPI card and click drill-down | Store breakdown table appears with correct data |

**Pass Criteria:** All 5 steps pass  
**Result:** [ ] Pass [ ] Fail [ ] Conditional  
**Tester Sign-off:** _________________ **Date:** _______

---

### TC-006: Store Manager Row-Level Security
**Related User Story:** US-06  
**Tester:** Tom (Store Manager, Store 14)  
**Priority:** High

| Step | Action | Expected Result |
|---|---|---|
| 1 | Log in to Power BI using Tom's credentials | Dashboard loads |
| 2 | Check revenue figure shown | Matches Store 14 revenue only — not company total |
| 3 | Attempt to change store filter to Store 15 | Filter is greyed out / not available |
| 4 | Inspect URL / query parameters | No other store data accessible via parameter manipulation |

**Pass Criteria:** Steps 2 and 3 both pass  
**Result:** [ ] Pass [ ] Fail [ ] Conditional  
**Tester Sign-off:** _________________ **Date:** _______

---

## Module 3: Customer Intelligence

### TC-007: RFM Segment Assignment
**Related User Story:** US-07, US-09  
**Tester:** James (Head of Marketing)  
**Priority:** Critical

| Step | Action | Expected Result |
|---|---|---|
| 1 | Select a known customer who purchased yesterday, 10 times total, £2,000 LTV | — |
| 2 | Query `mart_customer_rfm` for this customer | R=5, F≥4, M≥4, segment = 'Champions' |
| 3 | Select a known customer who last purchased 400 days ago | — |
| 4 | Query `mart_customer_rfm` for this customer | R=1, segment = 'Lost' |
| 5 | Check total customer count in RFM table | Matches total active customer count in CRM (within 1%) |

**Pass Criteria:** Steps 2 and 4 pass, Step 5 within tolerance  
**Result:** [ ] Pass [ ] Fail [ ] Conditional  
**Tester Sign-off:** _________________ **Date:** _______

---

### TC-008: Segment Export for CRM
**Related User Story:** US-07, US-08  
**Tester:** James (Head of Marketing)  
**Priority:** High

| Step | Action | Expected Result |
|---|---|---|
| 1 | Navigate to Customer Intelligence dashboard | — |
| 2 | Select "At Risk" segment | Customer list filters to At Risk only |
| 3 | Click Export button | CSV downloads with columns: customer_id, email_masked, segment, last_purchase_date, LTV |
| 4 | Verify email column | Emails are masked (e.g. j***@gmail.com) — full emails NOT exported |
| 5 | Upload CSV to Salesforce CRM test environment | Import succeeds, customers tagged as 'At Risk' in CRM |

**Pass Criteria:** All steps pass, especially Step 4 (GDPR compliance)  
**Result:** [ ] Pass [ ] Fail [ ] Conditional  
**Tester Sign-off:** _________________ **Date:** _______

---

## Module 4: Inventory & Forecasting

### TC-009: Stockout Alert
**Related User Story:** US-10  
**Tester:** Priya (Supply Chain Manager)  
**Priority:** Critical

| Step | Action | Expected Result |
|---|---|---|
| 1 | Open Inventory Dashboard | Dashboard loads in under 5 seconds |
| 2 | Check RAG status for SKU "JEAN-WOM-32-BLK" (set to 0 stock in test data) | Status = Red |
| 3 | Check email inbox (morning alert) | Daily stockout alert email lists this SKU |
| 4 | Filter dashboard to "Red status only" | Only SKUs at or below reorder point shown |
| 5 | Check forecasted demand column for Red SKUs | 7-day forecast values populated |

**Pass Criteria:** All 5 steps pass  
**Result:** [ ] Pass [ ] Fail [ ] Conditional  
**Tester Sign-off:** _________________ **Date:** _______

---

### TC-010: Demand Forecast Accuracy
**Related User Story:** US-11  
**Tester:** Priya (Supply Chain Manager)  
**Priority:** High

| Step | Action | Expected Result |
|---|---|---|
| 1 | Open Forecasting dashboard | 12-week forecast chart visible for each product category |
| 2 | Check confidence interval bands | 80% confidence interval shown as shaded area |
| 3 | Compare last 4 weeks of forecast vs actual (backtesting period) | MAPE displayed per category, ≤ 15% for ≥ 80% of categories |
| 4 | Check Christmas week forecast for Gifting category | Uplift visible — forecast higher than adjacent weeks |
| 5 | Verify forecast last updated date | Shows Monday of current week |

**Pass Criteria:** Step 3 accuracy target met, Steps 1, 2, 4, 5 pass  
**Result:** [ ] Pass [ ] Fail [ ] Conditional  
**Tester Sign-off:** _________________ **Date:** _______

---

## Module 5: Marketing Attribution

### TC-011: Channel Attribution Totals
**Related User Story:** US-12  
**Tester:** James (Head of Marketing)  
**Priority:** High

| Step | Action | Expected Result |
|---|---|---|
| 1 | Open Marketing Attribution dashboard | — |
| 2 | Check total attributed revenue across all channels | Sum of all channel attributed revenue equals total revenue for the period |
| 3 | Check ROAS for Paid Search | ROAS = Attributed Revenue / Spend — matches manual calculation |
| 4 | Switch from data-driven to last-click model | Revenue figures change to reflect last-click attribution |
| 5 | Export attribution report | CSV downloads with all channels and metrics |

**Pass Criteria:** Step 2 reconciliation passes, Step 3 calculation correct  
**Result:** [ ] Pass [ ] Fail [ ] Conditional  
**Tester Sign-off:** _________________ **Date:** _______

---

## UAT Sign-Off Summary

| Module | Test Cases | Passed | Failed | Conditional |
|---|---|---|---|---|
| Data Pipeline | TC-001 to TC-003 | | | |
| Executive Dashboard | TC-004 to TC-006 | | | |
| Customer Intelligence | TC-007 to TC-008 | | | |
| Inventory & Forecasting | TC-009 to TC-010 | | | |
| Marketing Attribution | TC-011 | | | |
| **Total** | **11** | | | |

---

## UAT Final Sign-Off

| Stakeholder | Role | Decision | Date |
|---|---|---|---|
| Emma Whitfield | CFO | [ ] Approved [ ] Rejected | |
| James Carter | Head of Marketing | [ ] Approved [ ] Rejected | |
| Priya Nair | Head of Data | [ ] Approved [ ] Rejected | |
| Mark Davies | IT Director | [ ] Approved [ ] Rejected | |
