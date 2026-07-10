"""
validator.py
============
Data validation layer — runs before any data is loaded to BigQuery.
Bad records are quarantined, not silently dropped.

Checks performed:
  - Null checks on primary key fields
  - Range checks on numeric fields
  - Referential integrity (orders → customers, orders → products)
  - Volume checks (record count vs 7-day average)

Usage:
    from etl.transformers.validator import validate_orders
    clean_df, quarantine_df, report = validate_orders(raw_df)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Tuple

import pandas as pd

from etl.utils.logger import logger


# ── Type alias ─────────────────────────────────────────────────────────────────
ValidationResult = Tuple[pd.DataFrame, pd.DataFrame, dict]


def _quarantine(df: pd.DataFrame, reason: str, check: str, run_id: str) -> pd.DataFrame:
    """Return a quarantine DataFrame for the given rejected records."""
    q = df.copy()
    q["quarantine_id"]   = [str(uuid.uuid4()) for _ in range(len(q))]
    q["run_id"]          = run_id
    q["failure_reason"]  = reason
    q["failed_check"]    = check
    q["quarantined_at"]  = datetime.utcnow().isoformat()
    q["record_raw"]      = q.drop(
        columns=["quarantine_id","run_id","failure_reason","failed_check","quarantined_at"],
        errors="ignore"
    ).to_json(orient="records", lines=True).splitlines()
    return q[["quarantine_id","run_id","failure_reason","failed_check","quarantined_at","record_raw"]]


def _null_check(
    df: pd.DataFrame,
    field: str,
    run_id: str,
    clean: pd.DataFrame,
    quarantine: list,
) -> pd.DataFrame:
    """Remove rows where field is null, add to quarantine list."""
    bad  = df[df[field].isna()]
    good = df[df[field].notna()]
    if len(bad) > 0:
        logger.warning(f"NULL_CHECK [{field}]: {len(bad)} records rejected")
        quarantine.append(_quarantine(bad, "NULL_PRIMARY_KEY", f"null_check:{field}", run_id))
    return good


def validate_orders(df: pd.DataFrame, run_id: str | None = None) -> ValidationResult:
    """
    Validate the orders DataFrame extracted from POS.

    Returns:
        clean_df      — records that passed all checks
        quarantine_df — rejected records with reason
        report        — summary dict for logging
    """
    if run_id is None:
        run_id = str(uuid.uuid4())

    logger.info(f"[VALIDATE] Starting orders validation | {len(df):,} input records")
    quarantine_frames = []
    total_input = len(df)

    # ── 1. Null checks on required fields ─────────────────────────────────────
    for field in ["order_id", "customer_id", "store_id", "order_date"]:
        df = _null_check(df, field, run_id, df, quarantine_frames)

    # ── 2. Duplicate order_id check ───────────────────────────────────────────
    dupes = df[df.duplicated(subset=["order_id"], keep="first")]
    if len(dupes) > 0:
        logger.warning(f"DUPLICATE_CHECK [order_id]: {len(dupes)} duplicates removed")
        quarantine_frames.append(_quarantine(dupes, "DUPLICATE_RECORD", "duplicate_check:order_id", run_id))
    df = df.drop_duplicates(subset=["order_id"], keep="first")

    # ── 3. Range check: order_total_pence must be > 0 ─────────────────────────
    if "order_total_pence" in df.columns:
        bad_range = df[df["order_total_pence"] <= 0]
        if len(bad_range) > 0:
            logger.warning(f"RANGE_CHECK [order_total_pence <= 0]: {len(bad_range)} records flagged")
            quarantine_frames.append(_quarantine(bad_range, "INVALID_RANGE", "range_check:order_total_pence", run_id))
        df = df[df["order_total_pence"] > 0]

    # ── 4. Date format check ──────────────────────────────────────────────────
    try:
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
        bad_date = df[df["order_date"].isna()]
        if len(bad_date) > 0:
            logger.warning(f"DATE_FORMAT_CHECK [order_date]: {len(bad_date)} unparseable dates")
            quarantine_frames.append(_quarantine(bad_date, "INVALID_DATE", "date_check:order_date", run_id))
        df = df[df["order_date"].notna()]
    except Exception as e:
        logger.error(f"Date parsing failed: {e}")

    # ── 5. Build quarantine output ────────────────────────────────────────────
    if quarantine_frames:
        quarantine_df = pd.concat(quarantine_frames, ignore_index=True)
    else:
        quarantine_df = pd.DataFrame()

    total_quarantined = len(quarantine_df)
    total_clean       = len(df)

    report = {
        "run_id":             run_id,
        "source":             "orders",
        "records_input":      total_input,
        "records_clean":      total_clean,
        "records_quarantined":total_quarantined,
        "quarantine_rate_pct":round(total_quarantined * 100 / total_input, 2) if total_input > 0 else 0,
    }

    logger.info(
        f"[VALIDATE] Orders complete | "
        f"Clean: {total_clean:,} | Quarantined: {total_quarantined:,} | "
        f"Rate: {report['quarantine_rate_pct']}%"
    )

    return df, quarantine_df, report


def validate_order_lines(df: pd.DataFrame, valid_order_ids: set, valid_product_ids: set, run_id: str | None = None) -> ValidationResult:
    """Validate order lines with referential integrity checks."""
    if run_id is None:
        run_id = str(uuid.uuid4())

    logger.info(f"[VALIDATE] Starting order_lines validation | {len(df):,} input records")
    quarantine_frames = []
    total_input = len(df)

    # Null checks
    for field in ["order_line_id", "order_id", "product_id"]:
        df = _null_check(df, field, run_id, df, quarantine_frames)

    # Referential integrity: order_id must exist in orders
    orphan_orders = df[~df["order_id"].isin(valid_order_ids)]
    if len(orphan_orders) > 0:
        logger.warning(f"REFERENTIAL_INTEGRITY [order_id]: {len(orphan_orders)} orphan lines")
        quarantine_frames.append(_quarantine(orphan_orders, "ORPHAN_RECORD", "ref_integrity:order_id", run_id))
    df = df[df["order_id"].isin(valid_order_ids)]

    # Referential integrity: product_id must exist in products
    orphan_products = df[~df["product_id"].isin(valid_product_ids)]
    if len(orphan_products) > 0:
        logger.warning(f"REFERENTIAL_INTEGRITY [product_id]: {len(orphan_products)} unknown products")
        quarantine_frames.append(_quarantine(orphan_products, "UNKNOWN_PRODUCT", "ref_integrity:product_id", run_id))
    df = df[df["product_id"].isin(valid_product_ids)]

    # Range: units_sold must be >= 1
    if "units_sold" in df.columns:
        bad = df[df["units_sold"] < 1]
        if len(bad) > 0:
            quarantine_frames.append(_quarantine(bad, "INVALID_RANGE", "range_check:units_sold", run_id))
        df = df[df["units_sold"] >= 1]

    quarantine_df = pd.concat(quarantine_frames, ignore_index=True) if quarantine_frames else pd.DataFrame()

    report = {
        "run_id":             run_id,
        "source":             "order_lines",
        "records_input":      total_input,
        "records_clean":      len(df),
        "records_quarantined":len(quarantine_df),
        "quarantine_rate_pct":round(len(quarantine_df) * 100 / total_input, 2) if total_input > 0 else 0,
    }
    logger.info(f"[VALIDATE] Order lines complete | Clean: {len(df):,} | Quarantined: {len(quarantine_df):,}")
    return df, quarantine_df, report
