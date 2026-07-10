"""
rfm_segmentation.py
====================
Runs RFM (Recency, Frequency, Monetary) customer segmentation.
Reads from raw CSV files in dev mode.
Outputs scored customer table with segment labels + 3 charts.

Usage:
    python analytics/segmentation/rfm_segmentation.py

Author: Uday Mourya
"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from etl.utils.logger import logger

# ── Config ─────────────────────────────────────────────────────────────────────
SAMPLE_CUSTOMERS = "data/raw/customers.csv"
OUTPUT_DIR       = "data/processed"
PLOTS_DIR        = "analytics/segmentation/plots"
ANALYSIS_DATE    = date.today()

os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Segment rules ──────────────────────────────────────────────────────────────

def assign_segment(r: int, f: int, m: int) -> str:
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 3 and m >= 3:
        return "Loyal Customers"
    if r >= 4 and f <= 2:
        return "New Customers"
    if r >= 3 and f >= 2 and m >= 2:
        return "Potential Loyalists"
    if r <= 2 and f >= 3 and m >= 3:
        return "At Risk"
    if r <= 2 and f >= 2:
        return "Needs Attention"
    if r == 1 and f <= 2:
        return "Lost"
    return "Others"


SEGMENT_COLOURS = {
    "Champions":            "#2ECC71",
    "Loyal Customers":      "#27AE60",
    "Potential Loyalists":  "#3498DB",
    "New Customers":        "#9B59B6",
    "Needs Attention":      "#F39C12",
    "At Risk":              "#E67E22",
    "Lost":                 "#E74C3C",
    "Others":               "#95A5A6",
}

SEGMENT_PRIORITY = {
    "Champions": 1, "Loyal Customers": 2, "Potential Loyalists": 3,
    "New Customers": 4, "Needs Attention": 5, "At Risk": 6, "Lost": 7, "Others": 8,
}


# ── Data loading ───────────────────────────────────────────────────────────────

def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("[RFM] Loading sample data from raw CSV files")
    orders    = pd.read_csv("data/raw/orders.csv")
    lines     = pd.read_csv("data/raw/order_lines.csv")
    sales     = lines.merge(
        orders[["order_id", "customer_id", "order_date", "store_id"]],
        on="order_id"
    )
    customers = pd.read_csv(SAMPLE_CUSTOMERS)
    logger.info(f"[RFM] Loaded {len(sales):,} order lines | {len(customers):,} customers")
    return sales, customers


# ── RFM calculation ────────────────────────────────────────────────────────────

def calculate_rfm(sales: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    logger.info("[RFM] Calculating RFM metrics")

    sales = sales.copy()
    sales.columns = sales.columns.str.lower()

    # Parse dates
    sales["order_date"] = pd.to_datetime(sales["order_date"])

    # Remove returns
    if "is_returned" in sales.columns:
        sales = sales[sales["is_returned"] != True]

    # Revenue column
    if "net_revenue_gbp" in sales.columns:
        rev_col = "net_revenue_gbp"
    else:
        sales["net_revenue_gbp"] = sales["net_revenue_pence"] / 100.0
        rev_col = "net_revenue_gbp"

    today = pd.Timestamp(ANALYSIS_DATE)

    rfm = sales.groupby("customer_id").agg(
        last_purchase_date  = ("order_date",      "max"),
        first_purchase_date = ("order_date",      "min"),
        purchase_frequency  = ("order_date",      pd.Series.nunique),
        total_orders        = ("order_id",        pd.Series.nunique),
        total_revenue_gbp   = (rev_col,           "sum"),
        avg_order_value_gbp = (rev_col,           "mean"),
    ).reset_index()

    rfm["days_since_last_purchase"] = (today - rfm["last_purchase_date"]).dt.days
    rfm["customer_age_days"]        = (today - rfm["first_purchase_date"]).dt.days
    rfm["total_revenue_gbp"]        = rfm["total_revenue_gbp"].round(2)
    rfm["avg_order_value_gbp"]      = rfm["avg_order_value_gbp"].round(2)

    # Score R, F, M 1–5 using quintiles
    rfm["r_score"] = pd.qcut(
        rfm["days_since_last_purchase"].rank(method="first"),
        q=5, labels=[5, 4, 3, 2, 1]
    ).astype(int)
    rfm["f_score"] = pd.qcut(
        rfm["purchase_frequency"].rank(method="first"),
        q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["m_score"] = pd.qcut(
        rfm["total_revenue_gbp"].rank(method="first"),
        q=5, labels=[1, 2, 3, 4, 5]
    ).astype(int)

    rfm["rfm_total_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]

    rfm["rfm_segment"] = rfm.apply(
        lambda row: assign_segment(row["r_score"], row["f_score"], row["m_score"]),
        axis=1
    )
    rfm["segment_priority"] = rfm["rfm_segment"].map(SEGMENT_PRIORITY)

    # Merge customer attributes
    customers = customers.copy()
    customers.columns = customers.columns.str.lower()
    rfm = rfm.merge(
        customers[["customer_id", "region", "loyalty_tier", "acquisition_channel"]],
        on="customer_id", how="left"
    )

    rfm["rfm_calculated_at"] = datetime.utcnow().isoformat()

    logger.info(f"[RFM] Complete — {len(rfm):,} customers scored")
    logger.info(f"[RFM] Segment distribution:\n{rfm['rfm_segment'].value_counts().to_string()}")

    return rfm.sort_values("segment_priority")


# ── Visualisations ─────────────────────────────────────────────────────────────

def plot_segment_distribution(rfm: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("RetailCo — Customer RFM Segmentation", fontsize=16, fontweight="bold")

    seg_counts = rfm.groupby("rfm_segment").agg(
        customer_count=("customer_id", "count"),
        total_revenue =("total_revenue_gbp", "sum"),
    ).sort_values("customer_count", ascending=False).reset_index()

    colours = [SEGMENT_COLOURS.get(s, "#95A5A6") for s in seg_counts["rfm_segment"]]

    axes[0].barh(seg_counts["rfm_segment"], seg_counts["customer_count"], color=colours)
    axes[0].set_xlabel("Number of Customers")
    axes[0].set_title("Customers per Segment")
    axes[0].invert_yaxis()
    for i, count in enumerate(seg_counts["customer_count"]):
        pct = count / len(rfm) * 100
        axes[0].text(count + 5, i, f"{count:,} ({pct:.1f}%)", va="center", fontsize=9)

    seg_rev = seg_counts.sort_values("total_revenue", ascending=False)
    axes[1].barh(
        seg_rev["rfm_segment"],
        seg_rev["total_revenue"] / 1_000,
        color=[SEGMENT_COLOURS.get(s, "#95A5A6") for s in seg_rev["rfm_segment"]]
    )
    axes[1].set_xlabel("Total Revenue (£000s)")
    axes[1].set_title("Revenue per Segment")
    axes[1].invert_yaxis()

    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "rfm_segment_distribution.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"[RFM] Plot saved: {path}")


def plot_rfm_heatmap(rfm: pd.DataFrame) -> None:
    pivot = rfm.pivot_table(
        values="total_revenue_gbp",
        index="r_score",
        columns="f_score",
        aggfunc="mean"
    ).round(0)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlOrRd",
                linewidths=0.5, ax=ax, cbar_kws={"label": "Avg Revenue (£)"})
    ax.set_title("Average Customer Revenue by Recency × Frequency Score", fontsize=13)
    ax.set_xlabel("Frequency Score (1=lowest, 5=highest)")
    ax.set_ylabel("Recency Score (1=longest ago, 5=most recent)")

    path = os.path.join(PLOTS_DIR, "rfm_heatmap.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"[RFM] Heatmap saved: {path}")


def plot_segment_scatter(rfm: pd.DataFrame) -> None:
    seg_summary = rfm.groupby("rfm_segment").agg(
        count  =("customer_id",         "count"),
        revenue=("total_revenue_gbp",   "sum"),
        avg_aov=("avg_order_value_gbp", "mean"),
    ).reset_index()

    fig, ax = plt.subplots(figsize=(12, 7))
    for _, row in seg_summary.iterrows():
        colour = SEGMENT_COLOURS.get(row["rfm_segment"], "#95A5A6")
        ax.scatter(row["count"], row["revenue"] / 1000,
                   s=row["avg_aov"] * 5, color=colour,
                   alpha=0.8, edgecolors="white", linewidths=1.5)
        ax.annotate(
            f"{row['rfm_segment']}\n{row['count']:,} customers",
            (row["count"], row["revenue"] / 1000),
            textcoords="offset points", xytext=(8, 4), fontsize=9
        )

    ax.set_xlabel("Number of Customers")
    ax.set_ylabel("Total Segment Revenue (£000s)")
    ax.set_title("RFM Segment: Size vs Revenue (bubble = avg order value)", fontsize=13)

    patches = [mpatches.Patch(color=v, label=k)
               for k, v in SEGMENT_COLOURS.items()
               if k in seg_summary["rfm_segment"].values]
    ax.legend(handles=patches, loc="upper left", fontsize=8)

    path = os.path.join(PLOTS_DIR, "rfm_segment_scatter.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    logger.info(f"[RFM] Scatter plot saved: {path}")


# ── Output ─────────────────────────────────────────────────────────────────────

def save_outputs(rfm: pd.DataFrame) -> None:
    out_path = os.path.join(OUTPUT_DIR, "mart_customer_rfm.csv")
    rfm.to_csv(out_path, index=False)
    logger.info(f"[RFM] Saved: {out_path} ({len(rfm):,} rows)")

    summary = rfm.groupby("rfm_segment").agg(
        customers     =("customer_id",              "count"),
        pct_of_base   =("customer_id",              lambda x: round(len(x) / len(rfm) * 100, 1)),
        total_revenue =("total_revenue_gbp",        "sum"),
        avg_ltv       =("total_revenue_gbp",        "mean"),
        avg_orders    =("total_orders",             "mean"),
        avg_days_since=("days_since_last_purchase", "mean"),
    ).round(2).sort_values("total_revenue", ascending=False)

    summary_path = os.path.join(OUTPUT_DIR, "rfm_segment_summary.csv")
    summary.to_csv(summary_path)
    logger.info(f"[RFM] Segment summary saved: {summary_path}")

    print("\n" + "=" * 65)
    print("  RFM SEGMENT SUMMARY")
    print("=" * 65)
    print(summary.to_string())
    print("=" * 65)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("[RFM] Starting RFM segmentation pipeline")
    sales, customers = load_data()
    rfm              = calculate_rfm(sales, customers)

    logger.info("[RFM] Generating visualisations")
    plot_segment_distribution(rfm)
    plot_rfm_heatmap(rfm)
    plot_segment_scatter(rfm)

    save_outputs(rfm)
    logger.info("[RFM] Pipeline complete")


if __name__ == "__main__":
    main()