# Stakeholder Matrix
## Enterprise Retail Analytics & Customer Intelligence Platform

---

| Field | Detail |
|---|---|
| **Version** | v1.0 |
| **Date** | June 2025 |
| **Author** | Uday Mourya, Analytics Engineer |

---

## Power / Interest Grid

```
High Power │ MANAGE CLOSELY         │ KEEP SATISFIED
           │  - CFO (Emma)          │  - IT Director (Mark)
           │  - Head of Data (Priya)│  - Legal / Compliance
           │  - CEO (James W.)      │
           │                        │
───────────┼────────────────────────┼──────────────────────────
           │ KEEP INFORMED          │ MONITOR
           │  - Head of Marketing   │  - Store Managers
           │  - Supply Chain Mgr    │  - Finance Team
Low Power  │  - Data Analyst (Lisa) │  - Marketing Executives
           │                        │
           └────────────────────────┴──────────────────────────
                  High Interest           Low Interest
```

---

## Detailed Stakeholder Profiles

### 1. James Whitfield — Chief Executive Officer
| Field | Detail |
|---|---|
| **Power** | High |
| **Interest** | High |
| **Engagement Strategy** | Manage Closely |
| **Primary Need** | Strategic KPI visibility; proof of ROI on the project |
| **Communication** | Monthly steering committee; executive summary report |
| **Influence on Project** | Ultimate sign-off authority; budget holder |
| **Potential Risk** | May request scope changes if competitor pressure increases |
| **Key Message** | This platform gives you real-time visibility to make faster, better decisions |

---

### 2. Sarah Chen — Chief Financial Officer
| Field | Detail |
|---|---|
| **Power** | High |
| **Interest** | High |
| **Engagement Strategy** | Manage Closely |
| **Primary Need** | Revenue, margin, and cost reporting; budget oversight of project |
| **Communication** | Bi-weekly dashboard demo; involved in UAT sign-off |
| **Influence on Project** | Approves project budget; defines financial KPI requirements |
| **Potential Risk** | May push back if BigQuery costs exceed projections |
| **Key Message** | Real-time P&L visibility and 80% reduction in finance reporting time |

---

### 3. Priya Nair — Head of Data & Analytics
| Field | Detail |
|---|---|
| **Power** | High |
| **Interest** | High |
| **Engagement Strategy** | Manage Closely |
| **Primary Need** | Platform built to enterprise standards; team upskilling; data governance |
| **Communication** | Daily stand-up; sprint planning and review; architecture reviews |
| **Influence on Project** | Technical approver; UAT lead; defines data standards |
| **Potential Risk** | Bandwidth constraints — also running two other data projects |
| **Key Message** | This becomes the foundation for all future analytics capability at RetailCo |

---

### 4. James Carter — Head of Marketing
| Field | Detail |
|---|---|
| **Power** | Medium |
| **Interest** | High |
| **Engagement Strategy** | Keep Informed |
| **Primary Need** | Attribution clarity; RFM segments exportable to CRM; campaign ROI |
| **Communication** | Weekly progress update; involved in Sprint 3 UAT |
| **Influence on Project** | Defines marketing analytics requirements; key UAT signatory |
| **Potential Risk** | May request real-time attribution — not in scope for Phase 1 |
| **Key Message** | You'll know exactly which channels are driving revenue and which customers to target |

---

### 5. Mark Davies — IT Director
| Field | Detail |
|---|---|
| **Power** | High |
| **Interest** | Low |
| **Engagement Strategy** | Keep Satisfied |
| **Primary Need** | Security and compliance; infrastructure fits IT standards; no technical debt |
| **Communication** | Monthly update; involved in architecture sign-off and security review |
| **Influence on Project** | Approves infrastructure; can block deployment if security concerns not resolved |
| **Potential Risk** | May delay API access provisioning if IT team is stretched |
| **Key Message** | Built on approved Google Cloud stack; GDPR-compliant; full audit trail |

---

### 6. Amy Thornton — Legal & Compliance Manager
| Field | Detail |
|---|---|
| **Power** | High |
| **Interest** | Low |
| **Engagement Strategy** | Keep Satisfied |
| **Primary Need** | GDPR compliance; PII handling documented; data retention policy enforced |
| **Communication** | Two formal reviews: initial architecture and pre-go-live |
| **Influence on Project** | Can block go-live if compliance requirements not met |
| **Potential Risk** | Data retention or consent requirements not addressed in design |
| **Key Message** | PII masked in analytics layer; data retention policies built in; full ICO compliance |

---

### 7. Rachel Singh — Supply Chain Manager
| Field | Detail |
|---|---|
| **Power** | Medium |
| **Interest** | High |
| **Engagement Strategy** | Keep Informed |
| **Primary Need** | Inventory visibility; demand forecasts; stockout alerts |
| **Communication** | Involved in Sprint 2 UAT; monthly check-in |
| **Influence on Project** | Key user; her adoption is critical to supply chain ROI case |
| **Potential Risk** | May not trust model forecasts and revert to spreadsheet habit |
| **Key Message** | Forecasts proven on 3-month backtest; MAPE under 15%; reduces stockouts |

---

### 8. Tom Bradley — Store Manager (Representative, 52 stores)
| Field | Detail |
|---|---|
| **Power** | Low |
| **Interest** | Low–Medium |
| **Engagement Strategy** | Monitor |
| **Primary Need** | Simple store dashboard; doesn't want complexity |
| **Communication** | 2 store manager focus groups during design phase; training session pre-launch |
| **Influence on Project** | End user satisfaction drives adoption metric |
| **Potential Risk** | Low digital literacy in some store managers; may resist change |
| **Key Message** | Your dashboard shows exactly how your store is performing vs target — one screen, 30 seconds |

---

### 9. Lisa Okafor — Data Analyst
| Field | Detail |
|---|---|
| **Power** | Low |
| **Interest** | High |
| **Engagement Strategy** | Keep Informed |
| **Primary Need** | Clean, documented data in BigQuery; dbt model documentation; self-service access |
| **Communication** | Involved in Sprint 1–2 testing; peer reviewer on dbt models |
| **Influence on Project** | Power user; early adopter who will champion platform internally |
| **Potential Risk** | May identify data quality issues not caught in validation layer |
| **Key Message** | All models documented in dbt; BigQuery access provisioned; no more waiting for data dumps |

---

## Communication Plan

| Stakeholder | Channel | Frequency | Content |
|---|---|---|---|
| CEO | Email summary + steering committee | Monthly | Executive summary, RAG status, key decisions needed |
| CFO | Dashboard demo + steering committee | Bi-weekly | Financial KPI progress, budget status |
| Head of Data | Daily stand-up | Daily | Sprint progress, blockers, technical decisions |
| Head of Marketing | Slack + sprint review | Weekly | Feature delivery, UAT dates |
| IT Director | Email | Monthly | Infrastructure updates, security sign-offs |
| Legal | Formal review meetings | x2 (architecture + pre-go-live) | GDPR compliance documentation |
| Supply Chain Manager | Email + UAT sessions | Sprint 2 onwards | Inventory/forecasting features |
| Store Managers | Focus groups + training | x2 + 1 pre-launch | Dashboard walkthrough |
| Data Analyst | Sprint ceremonies | Every sprint | Model documentation, access, data quality |
