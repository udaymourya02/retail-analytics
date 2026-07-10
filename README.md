# 🛒 Enterprise Retail Analytics & Customer Intelligence Platform

> End-to-end analytics platform consolidating sales, inventory, marketing, customer, and finance data for a national retail chain — built with Python, SQL, dbt, BigQuery, Power BI, and Looker Studio.

---

## 📌 Project Overview

| Item | Detail |
|---|---|
| **Domain** | Retail / E-commerce |
| **Type** | End-to-End Analytics Platform |
| **Role Simulated** | Data Analyst / BI Developer / Analytics Engineer |
| **Status** | In Progress |

### Business Problem
A national retail chain operates across 50+ stores and an online channel. Data is siloed across legacy POS systems, a CRM, a marketing platform, and a finance tool. Leadership cannot answer basic questions like:
- Which customers are at risk of churning?
- Which products should we restock before the weekend?
- Is our marketing spend actually driving revenue?

This platform consolidates all data sources into a single analytics layer, enabling real-time decisions across sales, inventory, marketing, and finance.

---

## 🏗️ Architecture

```
Data Sources → ETL Pipeline → BigQuery Data Warehouse → dbt Transforms → Dashboards
     │               │                  │                      │               │
 POS/CRM/API    Python Scripts     Star Schema           Staging/Marts    Power BI
 Marketing DB   REST API Calls     Raw → Processed       Business Logic   Looker Studio
 Finance ERP    Data Validation    Fact & Dim Tables      RFM / Forecast   Tableau
```

---

## 📁 Repository Structure

```
retail-analytics/
├── docs/
│   ├── business/          # BRD, FRD, Stakeholder Matrix, Risk Register
│   ├── technical/         # System design, data dictionary, API specs
│   └── diagrams/          # BPMN diagrams, ERDs, architecture diagrams
├── data/
│   ├── raw/               # Raw source data (CSV/JSON)
│   ├── processed/         # Cleaned, validated data
│   └── sample/            # Sample datasets for testing
├── etl/
│   ├── extractors/        # Pull data from APIs and source systems
│   ├── transformers/      # Clean, validate, enrich data
│   ├── loaders/           # Load into BigQuery
│   └── utils/             # Logging, config, helpers
├── sql/
│   ├── schema/            # DDL — table definitions
│   ├── queries/           # Ad hoc and scheduled queries
│   └── views/             # BigQuery views
├── dbt_project/
│   ├── models/
│   │   ├── staging/       # Raw → cleaned 1:1 models
│   │   ├── intermediate/  # Business logic joins
│   │   └── marts/         # Final analytics-ready tables
│   ├── tests/             # Data quality tests
│   └── macros/            # Reusable SQL macros
├── analytics/
│   ├── segmentation/      # RFM customer segmentation
│   ├── forecasting/       # Demand & sales forecasting
│   └── attribution/       # Marketing attribution models
├── dashboards/
│   ├── powerbi/           # Power BI files and documentation
│   ├── looker/            # Looker Studio reports
│   └── tableau/           # Tableau workbooks
├── automation/
│   ├── github_actions/    # CI/CD workflows
│   └── scripts/           # Scheduled job scripts
├── notebooks/             # EDA and analysis Jupyter notebooks
├── tests/                 # Unit and integration tests
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🔧 Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11, SQL |
| **Data Warehouse** | Google BigQuery |
| **Transformations** | dbt Core |
| **Orchestration** | GitHub Actions |
| **BI / Dashboards** | Power BI, Looker Studio, Tableau |
| **Version Control** | Git / GitHub |
| **Containerisation** | Docker |
| **APIs** | REST (requests, FastAPI) |
| **Libraries** | pandas, scikit-learn, prophet, sqlalchemy |

---

## 📊 Features Built

- [x] Project structure and architecture design
- [ ] Business requirements documentation (BRD, FRD)
- [ ] Star schema data warehouse design
- [ ] Synthetic retail dataset generation
- [ ] ETL pipeline (extract → transform → load)
- [ ] dbt staging and marts models
- [ ] RFM customer segmentation
- [ ] Sales & demand forecasting (Prophet)
- [ ] Marketing attribution model
- [ ] Executive KPI dashboard (Power BI)
- [ ] Inventory optimisation analysis
- [ ] Automated reporting pipeline
- [ ] Data quality checks
- [ ] CI/CD via GitHub Actions

---

## 📄 Business Documents

| Document | Description | Location |
|---|---|---|
| BRD | Business Requirements Document | `docs/business/BRD.md` |
| FRD | Functional Requirements Document | `docs/business/FRD.md` |
| User Stories | Agile user stories by persona | `docs/business/UserStories.md` |
| BPMN Diagrams | Process flow diagrams | `docs/diagrams/` |
| UAT Test Cases | User Acceptance Testing scripts | `docs/business/UAT_TestCases.md` |
| Risk Register | Project and data risks | `docs/business/RiskRegister.md` |
| Stakeholder Matrix | Stakeholder mapping | `docs/business/StakeholderMatrix.md` |

---

## 🚀 Getting Started

```bash
# Clone the repo
git clone https://github.com/udaymourya02/retail-analytics.git
cd retail-analytics

# Install dependencies
pip install -r requirements.txt

# Generate sample data
python data/sample/generate_data.py

# Run ETL pipeline
python etl/main.py

# Run dbt models
cd dbt_project && dbt run && dbt test
```

---

## 👤 Author

**Uday Mourya**  
MSc Business Analytics — University of Warwick (2026)  
[LinkedIn](https://linkedin.com/in/udaymourya) | [GitHub](https://github.com/udaymourya02)

---
*Built as a portfolio project demonstrating end-to-end analytics engineering and BI capabilities.*
