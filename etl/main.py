"""
main.py
=======
Main ETL pipeline orchestrator for the RetailCo Analytics Platform.

Execution order:
  1. Extract from all source systems (or sample CSV files in dev)
  2. Validate all extracted data
  3. Transform into warehouse schema
  4. Load to BigQuery
  5. Log pipeline run results

Usage:
    # Development (uses sample CSV data)
    python etl/main.py

    # Production (uses live APIs)
    USE_SAMPLE_DATA=false python etl/main.py

Author: Uday Mourya
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime

import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.utils.config import config
from etl.utils.logger import logger
from etl.transformers.validator import validate_orders, validate_order_lines
from etl.transformers.transform import (
    transform_customers,
    transform_products,
    transform_stores,
    transform_orders,
    transform_inventory,
    transform_marketing,
)

# ── Conditional imports ────────────────────────────────────────────────────────
if not config.USE_SAMPLE_DATA:
    from etl.loaders.bigquery_loader import BigQueryLoader


# ── Sample data loader (dev mode) ─────────────────────────────────────────────

def load_sample_data() -> dict[str, pd.DataFrame]:
    """Load synthetic CSV files from data/raw/ for local development."""
    base = config.SAMPLE_DATA_DIR
    logger.info(f"[MAIN] Loading sample data from {base}/")

    files = {
        "customers":     "customers.csv",
        "products":      "products.csv",
        "stores":        "stores.csv",
        "orders":        "orders.csv",
        "order_lines":   "order_lines.csv",
        "inventory":     "inventory.csv",
        "marketing":     "marketing_spend.csv",
    }

    data = {}
    for key, fname in files.items():
        path = os.path.join(base, fname)
        if os.path.exists(path):
            data[key] = pd.read_csv(path)
            logger.info(f"  ✓ {fname}: {len(data[key]):,} rows")
        else:
            logger.warning(f"  ✗ {fname} not found — run data/sample/generate_data.py first")
            data[key] = pd.DataFrame()

    return data


# ── Pipeline stages ────────────────────────────────────────────────────────────

def run_pipeline() -> None:
    """Full ETL pipeline — extract, validate, transform, load."""

    run_id     = str(uuid.uuid4())
    started_at = datetime.utcnow()
    logger.info("=" * 60)
    logger.info(f"  RETAILCO ETL PIPELINE STARTING")
    logger.info(f"  Run ID : {run_id}")
    logger.info(f"  Started: {started_at.isoformat()}")
    logger.info(f"  Mode   : {'SAMPLE DATA' if config.USE_SAMPLE_DATA else 'PRODUCTION'}")
    logger.info("=" * 60)

    all_quarantine = []
    summary        = {}

    # ── STAGE 1: EXTRACT ──────────────────────────────────────────────────────
    logger.info("[STAGE 1] Extract")
    if config.USE_SAMPLE_DATA:
        raw = load_sample_data()
    else:
        # Production: import and call live API extractors
        from etl.extractors.pos_extractor       import extract_pos
        from etl.extractors.crm_extractor       import extract_crm
        from etl.extractors.wms_extractor       import extract_wms
        from etl.extractors.marketing_extractor import extract_marketing
        raw = {
            "orders":       extract_pos(),
            "order_lines":  extract_pos(lines=True),
            "customers":    extract_crm(),
            "products":     extract_crm(products=True),
            "stores":       extract_crm(stores=True),
            "inventory":    extract_wms(),
            "marketing":    extract_marketing(),
        }

    # ── STAGE 2: VALIDATE ─────────────────────────────────────────────────────
    logger.info("[STAGE 2] Validate")

    # Validate orders
    clean_orders, q_orders, report_orders = validate_orders(raw["orders"], run_id)
    all_quarantine.append(q_orders)
    summary["orders"] = report_orders

    # Validate order lines (with referential integrity)
    valid_order_ids   = set(clean_orders["order_id"].dropna())
    valid_product_ids = set(raw["products"]["product_id"].dropna())
    clean_lines, q_lines, report_lines = validate_order_lines(
        raw["order_lines"], valid_order_ids, valid_product_ids, run_id
    )
    all_quarantine.append(q_lines)
    summary["order_lines"] = report_lines

    # ── STAGE 3: TRANSFORM ────────────────────────────────────────────────────
    logger.info("[STAGE 3] Transform")

    dim_customers = transform_customers(raw["customers"])
    dim_products  = transform_products(raw["products"])
    dim_stores    = transform_stores(raw["stores"])
    fact_sales    = transform_orders(
        clean_orders, clean_lines, dim_customers, dim_products, dim_stores, run_id
    )
    fact_inventory = transform_inventory(raw["inventory"], dim_products, dim_stores, run_id)
    fact_marketing = transform_marketing(raw["marketing"], run_id)

    # ── STAGE 4: LOAD (or save to CSV in dev) ─────────────────────────────────
    logger.info("[STAGE 4] Load")

    if config.USE_SAMPLE_DATA:
        # In dev mode: save processed files to data/processed/ for inspection
        out_dir = "data/processed"
        os.makedirs(out_dir, exist_ok=True)

        dim_customers.to_csv(f"{out_dir}/dim_customer.csv",  index=False)
        dim_products.to_csv(f"{out_dir}/dim_product.csv",    index=False)
        dim_stores.to_csv(f"{out_dir}/dim_store.csv",        index=False)
        fact_sales.to_csv(f"{out_dir}/fact_sales.csv",       index=False)
        fact_inventory.to_csv(f"{out_dir}/fact_inventory.csv",index=False)
        fact_marketing.to_csv(f"{out_dir}/fact_marketing.csv",index=False)

        # Quarantine
        all_q = pd.concat([q for q in all_quarantine if q is not None and len(q) > 0], ignore_index=True) if any(len(q) > 0 for q in all_quarantine if q is not None) else pd.DataFrame()
        if not all_q.empty:
            all_q.to_csv(f"{out_dir}/quarantine.csv", index=False)

        logger.info(f"[LOAD] Dev mode — outputs written to {out_dir}/")

    else:
        # Production: load to BigQuery
        loader = BigQueryLoader()
        loader.load(dim_customers,  "dim_customer",           write_disposition="WRITE_TRUNCATE")
        loader.load(dim_products,   "dim_product",            write_disposition="WRITE_TRUNCATE")
        loader.load(dim_stores,     "dim_store",              write_disposition="WRITE_TRUNCATE")
        loader.load(fact_sales,     "fact_sales",             write_disposition="WRITE_APPEND")
        loader.load(fact_inventory, "fact_inventory",         write_disposition="WRITE_APPEND")
        loader.load(fact_marketing, "fact_marketing_spend",   write_disposition="WRITE_APPEND")

        all_q = pd.concat([q for q in all_quarantine if not q.empty], ignore_index=True)
        loader.load_quarantine(all_q, run_id)

        loader.log_pipeline_run(
            run_id=run_id,
            source_system="ALL",
            records_extracted=sum(r.get("records_input", 0) for r in summary.values()),
            records_loaded=sum(r.get("records_clean", 0) for r in summary.values()),
            records_quarantined=sum(r.get("records_quarantined", 0) for r in summary.values()),
            status="SUCCESS",
            started_at=started_at,
        )

    # ── STAGE 5: SUMMARY ──────────────────────────────────────────────────────
    duration = (datetime.utcnow() - started_at).total_seconds()
    logger.info("=" * 60)
    logger.info("  PIPELINE COMPLETE")
    logger.info(f"  Duration : {duration:.1f}s")
    logger.info(f"  Orders   : {len(clean_orders):,} clean / {len(q_orders):,} quarantined")
    logger.info(f"  Lines    : {len(clean_lines):,} clean / {len(q_lines):,} quarantined")
    logger.info(f"  fact_sales rows : {len(fact_sales):,}")
    logger.info("=" * 60)


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline()
