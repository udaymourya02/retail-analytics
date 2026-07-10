# Risk Register
## Enterprise Retail Analytics & Customer Intelligence Platform

---

| Field | Detail |
|---|---|
| **Version** | v1.0 |
| **Date** | June 2025 |
| **Author** | Uday Mourya, Analytics Engineer |
| **Review Frequency** | Fortnightly (every sprint review) |

---

## Risk Scoring Matrix

| | **Low Impact (1)** | **Medium Impact (2)** | **High Impact (3)** |
|---|---|---|---|
| **Low Likelihood (1)** | 1 — Low | 2 — Low | 3 — Medium |
| **Medium Likelihood (2)** | 2 — Low | 4 — Medium | 6 — High |
| **High Likelihood (3)** | 3 — Medium | 6 — High | 9 — Critical |

**Score = Likelihood × Impact**

---

## Risk Register

### RISK-001: Source System API Unavailability
| Field | Detail |
|---|---|
| **Category** | Technical |
| **Description** | POS or CRM API becomes unavailable, causing pipeline failure and stale dashboards |
| **Likelihood** | 2 — Medium |
| **Impact** | 3 — High |
| **Risk Score** | 6 — High |
| **Owner** | Data Engineer |
| **Mitigation** | Implement retry logic with exponential backoff; cache last successful extract; alert within 5 mins of failure; manual fallback CSV extract documented |
| **Contingency** | IT team to provide CSV export of daily POS data if API down > 4 hours |
| **Status** | Open |

---

### RISK-002: Data Quality Issues from Legacy POS System
| Field | Detail |
|---|---|
| **Category** | Data |
| **Description** | Legacy POS system exports data with inconsistent formatting, duplicate records, or missing fields, corrupting downstream analytics |
| **Likelihood** | 3 — High |
| **Impact** | 3 — High |
| **Risk Score** | 9 — Critical |
| **Owner** | Uday Mourya (Analytics Engineer) |
| **Mitigation** | Comprehensive data validation layer before warehouse load; quarantine table for rejected records; data profiling in Sprint 1 to identify known issues; weekly DQ report to data team |
| **Contingency** | Rollback to prior day's warehouse snapshot if DQ failure rate exceeds 5% |
| **Status** | Open — Monitoring |

---

### RISK-003: GDPR Non-Compliance (Customer PII Exposure)
| Field | Detail |
|---|---|
| **Category** | Compliance / Legal |
| **Description** | Customer PII (name, email, address) exposed in analytics layer, violating GDPR and ICO requirements |
| **Likelihood** | 2 — Medium |
| **Impact** | 3 — High |
| **Risk Score** | 6 — High |
| **Owner** | IT Director / Data Engineer |
| **Mitigation** | PII fields masked at staging layer (before marts); column-level access controls in BigQuery; GDPR data mapping documented; privacy review by legal team before go-live |
| **Contingency** | Immediate data masking rollback; ICO notification within 72 hours if breach confirmed |
| **Status** | Open — Legal review in progress |

---

### RISK-004: BigQuery Cost Overrun
| Field | Detail |
|---|---|
| **Category** | Financial |
| **Description** | Unoptimised queries or unexpected data volume causes Google Cloud billing to exceed budget |
| **Likelihood** | 2 — Medium |
| **Impact** | 2 — Medium |
| **Risk Score** | 4 — Medium |
| **Owner** | Data Engineer |
| **Mitigation** | Query cost estimation before production deployment; BigQuery cost controls and budget alerts set at 80% and 100% of monthly limit; table partitioning and clustering implemented; dbt incremental models to avoid full-table scans |
| **Contingency** | Pause non-critical scheduled queries; escalate to Head of Data if 80% alert triggers |
| **Status** | Open |

---

### RISK-005: Stakeholder Adoption Failure
| Field | Detail |
|---|---|
| **Category** | People / Change |
| **Description** | Business stakeholders continue using Excel reports instead of dashboards, undermining ROI of the project |
| **Likelihood** | 2 — Medium |
| **Impact** | 2 — Medium |
| **Risk Score** | 4 — Medium |
| **Owner** | Head of Data (Priya Nair) |
| **Mitigation** | Stakeholders involved in dashboard design (not just sign-off); training sessions 2 weeks before go-live; dashboard embedded in existing team meeting rhythms; executive sponsor to mandate dashboard use for monthly reviews |
| **Contingency** | Identify champion users per department; gather feedback after 30 days and iterate |
| **Status** | Open |

---

### RISK-006: Key Person Dependency
| Field | Detail |
|---|---|
| **Category** | Resource |
| **Description** | Analytics platform knowledge concentrated in one person; project delivery or maintenance at risk if that person is unavailable |
| **Likelihood** | 2 — Medium |
| **Impact** | 3 — High |
| **Risk Score** | 6 — High |
| **Owner** | Head of Data |
| **Mitigation** | All code documented and version-controlled in GitHub; architecture decision records (ADRs) written; knowledge transfer sessions with at least one other team member per sprint; runbooks written for all operational procedures |
| **Contingency** | Contractor sourced within 1 week if key engineer unavailable for > 5 days |
| **Status** | Open |

---

### RISK-007: Forecast Model Inaccuracy
| Field | Detail |
|---|---|
| **Category** | Technical / Business |
| **Description** | Demand forecasting model produces inaccurate predictions, leading to poor purchasing decisions and inventory issues |
| **Likelihood** | 2 — Medium |
| **Impact** | 2 — Medium |
| **Risk Score** | 4 — Medium |
| **Owner** | Uday Mourya (Analytics Engineer) |
| **Mitigation** | Model evaluated on 3-month backtesting period before production; MAPE target ≤ 15%; forecast accuracy dashboard visible to supply chain team; model retrained monthly with fresh data |
| **Contingency** | Fall back to simple moving average if Prophet MAPE > 20%; flag to supply chain to apply manual judgment |
| **Status** | Open |

---

### RISK-008: GitHub Actions / CI/CD Pipeline Failure
| Field | Detail |
|---|---|
| **Category** | Technical |
| **Description** | Automated CI/CD pipeline fails, blocking code deployments or causing untested code to reach production |
| **Likelihood** | 1 — Low |
| **Impact** | 2 — Medium |
| **Risk Score** | 2 — Low |
| **Owner** | Data Engineer |
| **Mitigation** | Branch protection rules enforce CI pass before merge; manual deployment procedure documented as fallback; GitHub status page monitored |
| **Contingency** | Manual deployment from local environment using documented runbook |
| **Status** | Open |

---

### RISK-009: Scope Creep
| Field | Detail |
|---|---|
| **Category** | Project Management |
| **Description** | Stakeholders request additional features mid-project, causing timeline slippage and missed MVP deadline |
| **Likelihood** | 3 — High |
| **Impact** | 2 — Medium |
| **Risk Score** | 6 — High |
| **Owner** | Project Sponsor (Head of Data) |
| **Mitigation** | Change control process documented; all new requests logged in product backlog and prioritised in sprint planning; MVP scope locked with executive sponsor sign-off; fortnightly steering committee reviews progress |
| **Contingency** | Defer new requests to Phase 2; escalate to executive sponsor if stakeholder insists |
| **Status** | Open — Monitoring |

---

## Risk Summary

| Risk ID | Description | Score | Rating | Status |
|---|---|---|---|---|
| RISK-001 | API Unavailability | 6 | High | Open |
| RISK-002 | Legacy Data Quality | 9 | Critical | Monitoring |
| RISK-003 | GDPR / PII Exposure | 6 | High | Legal Review |
| RISK-004 | BigQuery Cost Overrun | 4 | Medium | Open |
| RISK-005 | Stakeholder Adoption | 4 | Medium | Open |
| RISK-006 | Key Person Dependency | 6 | High | Open |
| RISK-007 | Forecast Inaccuracy | 4 | Medium | Open |
| RISK-008 | CI/CD Failure | 2 | Low | Open |
| RISK-009 | Scope Creep | 6 | High | Monitoring |
