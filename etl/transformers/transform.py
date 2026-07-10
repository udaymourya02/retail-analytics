"""
transform.py
============
Transforms validated raw data into warehouse-ready DataFrames.
Handles type casting, standardisation, and surrogate key generation.

Author: Uday Mourya
"""

from __future__ import annotations

import hashlib
from datetime import datetime

import pandas as pd

from etl.utils.logger import logger


def _make_surrogate_key(natural_key: str) -> int:
    """Deterministic integer surrogate key from a natural key string."""
    return int(hashlib.md5(natural_key.encode()).hexdigest(), 16) % (10**9)


# ── Dimension transforms ───────────────────────────────────────────────────────

def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and enrich customers for dim_customer."""
    logger.info(f"[TRANSFORM] Customers: {len(df):,} rows")

    out = df.copy()

    # Surrogate key
    out["customer_key"] = out["customer_id"].apply(_make_surrogate_key)

    # Standardise strings
    for col in ["gender", "age_band", "loyalty_tier", "region", "city"]:
        if col in out.columns:
            out[col] = out[col].str.strip().str.title()

    # Dates
    out["acquisition_date"] = pd.to_datetime(out["acquisition_date"], errors="coerce").dt.date

    # SCD Type 2 columns
    now = datetime.utcnow()
    out["valid_from"]  = now.date()
    out["valid_to"]    = None
    out["is_current"]  = True
    out["created_at"]  = now
    out["updated_at"]  = now

    # Default RFM fields to null (populated by analytics layer)
    for rfm_col in ["rfm_recency_score","rfm_frequency_score","rfm_monetary_score","rfm_segment","rfm_updated_at","customer_ltv_gbp"]:
        if rfm_col not in out.columns:
            out[rfm_col] = None

    logger.info(f"[TRANSFORM] Customers complete: {len(out):,} rows")
    return out


def transform_products(df: pd.DataFrame) -> pd.DataFrame:
    """Clean products for dim_product."""
    logger.info(f"[TRANSFORM] Products: {len(df):,} rows")

    out = df.copy()
    out["product_key"] = out["product_id"].apply(_make_surrogate_key)

    out["category"]    = out["category"].str.strip().str.title()
    out["subcategory"] = out["subcategory"].str.strip().str.title()
    out["is_active"]   = out["is_active"].astype(bool)
    out["launch_date"] = pd.to_datetime(out["launch_date"], errors="coerce").dt.date

    now = datetime.utcnow()
    out["valid_from"] = now.date()
    out["valid_to"]   = None
    out["is_current"] = True
    out["created_at"] = now
    out["updated_at"] = now

    return out


def transform_stores(df: pd.DataFrame) -> pd.DataFrame:
    """Clean stores for dim_store."""
    out = df.copy()
    out["store_key"]    = out["store_id"].apply(_make_surrogate_key)
    out["opening_date"] = pd.to_datetime(out["opening_date"], errors="coerce").dt.date
    out["is_active"]    = out["is_active"].astype(bool)
    out["country"]      = "United Kingdom"

    now = datetime.utcnow()
    out["valid_from"] = now.date()
    out["valid_to"]   = None
    out["is_current"] = True
    out["created_at"] = now
    out["updated_at"] = now
    return out


# ── Fact transforms ────────────────────────────────────────────────────────────

def transform_orders(
    orders_df: pd.DataFrame,
    lines_df:  pd.DataFrame,
    customers_df: pd.DataFrame,
    products_df:  pd.DataFrame,
    stores_df:    pd.DataFrame,
    pipeline_run_id: str,
) -> pd.DataFrame:
    """
    Joins orders + order_lines + dimension keys to produce fact_sales rows.
    One row per order line item.
    """
    logger.info(f"[TRANSFORM] Building fact_sales from {len(lines_df):,} order lines")

    # Build lookup maps
    cust_key_map = dict(zip(customers_df["customer_id"], customers_df["customer_key"]))
    prod_key_map = dict(zip(products_df["product_id"],   products_df["product_key"]))
    store_key_map= dict(zip(stores_df["store_id"],       stores_df["store_key"]))

    # Merge lines with orders
    fact = lines_df.merge(orders_df, on="order_id", how="left")

    # Map dimension keys
    fact["customer_key"] = fact["customer_id"].map(cust_key_map)
    fact["product_key"]  = fact["product_id"].map(prod_key_map)
    fact["store_key"]    = fact["store_id"].map(store_key_map)

    # Date key (YYYYMMDD integer)
    fact["order_date"]   = pd.to_datetime(fact["order_date"], errors="coerce")
    fact["date_key"]     = fact["order_date"].dt.strftime("%Y%m%d").astype("Int64")

    # Channel key (hardcoded small lookup)
    channel_map = {"Online": 1, "In-Store": 2, "App": 3, "Wholesale": 4}
    fact["channel_key"]  = fact["channel"].map(channel_map).fillna(99).astype(int)

    # Campaign key (simple hash, nullable)
    fact["campaign_key"] = fact["campaign_id"].apply(
        lambda x: _make_surrogate_key(str(x)) if pd.notna(x) else None
    )

    # Surrogate sale key
    fact["sale_key"] = fact["order_line_id"].apply(_make_surrogate_key)

    # Audit
    now = datetime.utcnow()
    fact["source_system"]    = "POS"
    fact["pipeline_run_id"]  = pipeline_run_id
    fact["created_at"]       = now
    fact["updated_at"]       = now

    # Select only warehouse columns
    cols = [
        "sale_key","order_id","order_line_id",
        "date_key","customer_key","product_key","store_key","channel_key","campaign_key",
        "units_sold","gross_revenue_pence","discount_pence","net_revenue_pence",
        "cost_of_goods_pence","gross_profit_pence",
        "is_returned","return_date",
        "source_system","pipeline_run_id","created_at","updated_at",
    ]
    fact = fact[[c for c in cols if c in fact.columns]]

    logger.info(f"[TRANSFORM] fact_sales complete: {len(fact):,} rows")
    return fact


def transform_inventory(df: pd.DataFrame, products_df: pd.DataFrame, stores_df: pd.DataFrame, pipeline_run_id: str) -> pd.DataFrame:
    """Transform inventory snapshot for fact_inventory."""
    logger.info(f"[TRANSFORM] Inventory: {len(df):,} rows")

    prod_key_map  = dict(zip(products_df["product_id"], products_df["product_key"]))
    store_key_map = dict(zip(stores_df["store_id"],     stores_df["store_key"]))

    out = df.copy()
    out["product_key"] = out["product_id"].map(prod_key_map)
    out["store_key"]   = out["store_id"].map(store_key_map)
    out["date_key"]    = pd.to_datetime(out["snapshot_date"]).dt.strftime("%Y%m%d").astype("Int64")

    out["inventory_key"]    = (out["product_id"] + out["store_id"] + out["snapshot_date"]).apply(_make_surrogate_key)
    out["pipeline_run_id"]  = pipeline_run_id
    out["created_at"]       = datetime.utcnow()

    return out


def transform_marketing(df: pd.DataFrame, pipeline_run_id: str) -> pd.DataFrame:
    """Transform marketing spend for fact_marketing_spend."""
    out = df.copy()
    out["date_key"]       = pd.to_datetime(out["date"]).dt.strftime("%Y%m%d").astype("Int64")
    out["campaign_key"]   = out["campaign_id"].apply(_make_surrogate_key)
    out["spend_key"]      = (out["campaign_id"] + out["date"]).apply(_make_surrogate_key)

    # Derived metrics
    out["ctr"]      = out["clicks"] / out["impressions"].replace(0, pd.NA)
    out["cpc_pence"]= (out["spend_pence"] / out["clicks"].replace(0, pd.NA)).fillna(0).round(0).astype(int)
    out["roas"]     = out["attributed_revenue_pence"] / out["spend_pence"].replace(0, pd.NA)

    out["pipeline_run_id"] = pipeline_run_id
    out["created_at"]      = datetime.utcnow()
    return out
