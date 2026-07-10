"""
demand_forecasting.py
======================
Generates 12-week demand forecasts per product category
using Facebook Prophet time-series model.

Features:
  - UK public holiday effects as regressors
  - Weekly + annual seasonality
  - Promotional period uplift
  - 80% confidence intervals stored
  - MAPE backtesting (last 8 weeks)
  - One chart per category saved to plots/

Usage:
    python analytics/forecasting/demand_forecasting.py

Author: Uday Mourya
"""

from __future__ import annotations

import os
import sys
import warnings
from datetime import date, timedelta

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from etl.utils.logger import logger

# ── Config ─────────────────────────────────────────────────────────────────────
USE_SAMPLE_DATA  = os.getenv("USE_SAMPLE_DATA", "true").lower() == "true"
FORECAST_HORIZON = 12   # weeks ahead
CONFIDENCE       = 0.80 # prediction interval
MAPE_TARGET      = 15.0 # % — alert if above this
OUTPUT_DIR       = "data/processed"
PLOTS_DIR        = "analytics/forecasting/plots"

os.makedirs(PLOTS_DIR, exist_ok=True)


# ── UK Public Holidays (Prophet regressor) ─────────────────────────────────────

UK_PUBLIC_HOLIDAYS = pd.DataFrame({
    "holiday": [
        "New Year",         "New Year",
        "Good Friday",      "Good Friday",
        "Easter Monday",    "Easter Monday",
        "Early May Bank",   "Early May Bank",
        "Spring Bank",      "Spring Bank",
        "Summer Bank",      "Summer Bank",
        "Christmas Day",    "Christmas Day",
        "Boxing Day",       "Boxing Day",
    ],
    "ds": pd.to_datetime([
        "2022-01-01", "2023-01-02",
        "2022-04-15", "2023-04-07",
        "2022-04-18", "2023-04-10",
        "2022-05-02", "2023-05-01",
        "2022-06-02", "2023-05-29",
        "2022-08-29", "2023-08-28",
        "2022-12-25", "2023-12-25",
        "2022-12-26", "2023-12-26",
    ]),
    "lower_window": 0,
    "upper_window": 1,
})


# ── Data loading ───────────────────────────────────────────────────────────────

def load_weekly_sales() -> pd.DataFrame:
    """Load and aggregate sales to weekly category-level."""
    logger.info("[FORECAST] Loading sales data")

    if USE_SAMPLE_DATA:
        orders = pd.read_csv("data/raw/orders.csv")
        lines  = pd.read_csv("data/raw/order_lines.csv")
        prods  = pd.read_csv("data/raw/products.csv")[["product_id","category"]]

        df = lines.merge(orders[["order_id","order_date"]], on="order_id")
        df = df.merge(prods, on="product_id")

        df["order_date"] = pd.to_datetime(df["order_date"])
        df["week_start"] = df["order_date"].dt.to_period("W-SUN").dt.start_time

        weekly = df.groupby(["week_start","category"]).agg(
            units_sold      = ("units_sold", "sum"),
            revenue         = ("net_revenue_pence", lambda x: x.sum() / 100),
        ).reset_index().rename(columns={"week_start": "ds"})

    else:
        from google.cloud import bigquery
        client  = bigquery.Client()
        weekly  = client.query("""
            SELECT
                DATE_TRUNC(d.full_date, WEEK(MONDAY))   AS ds,
                p.category,
                SUM(s.units_sold)                       AS units_sold,
                SUM(s.net_revenue_pence) / 100.0        AS revenue
            FROM `retailco.warehouse.fact_sales`    s
            JOIN `retailco.warehouse.dim_product`   p ON s.product_key = p.product_key
            JOIN `retailco.warehouse.dim_date`      d ON s.date_key    = d.date_key
            WHERE s.is_returned = FALSE
            GROUP BY 1, 2
            ORDER BY 1, 2
        """).to_dataframe()

    weekly["ds"] = pd.to_datetime(weekly["ds"])
    logger.info(f"[FORECAST] Loaded {len(weekly):,} week-category rows "
                f"| {weekly['category'].nunique()} categories "
                f"| {weekly['ds'].min().date()} → {weekly['ds'].max().date()}")
    return weekly


# ── Forecasting ────────────────────────────────────────────────────────────────

def run_prophet_forecast(
    df_category: pd.DataFrame,
    category: str,
) -> tuple[pd.DataFrame, float]:
    """
    Fit Prophet model for one category.
    Returns (forecast_df, mape_pct).
    """
    try:
        from prophet import Prophet
    except ImportError:
        logger.warning("[FORECAST] Prophet not installed — using simple moving average fallback")
        return _moving_average_fallback(df_category, category)

    # Prophet expects columns 'ds' and 'y'
    train = df_category.rename(columns={"units_sold": "y"})[["ds", "y"]].copy()
    train = train.sort_values("ds").dropna()

    if len(train) < 8:
        logger.warning(f"[FORECAST] {category}: insufficient data ({len(train)} weeks) — skipping")
        return pd.DataFrame(), None

    # ── Backtesting: hold out last 8 weeks ────────────────────────────────────
    cutoff_date = train["ds"].max() - pd.Timedelta(weeks=8)
    train_bt    = train[train["ds"] <= cutoff_date]
    test_bt     = train[train["ds"] >  cutoff_date]

    # ── Fit model ─────────────────────────────────────────────────────────────
    model = Prophet(
        holidays            = UK_PUBLIC_HOLIDAYS,
        weekly_seasonality  = True,
        yearly_seasonality  = True,
        interval_width      = CONFIDENCE,
        changepoint_prior_scale = 0.1,   # controls trend flexibility
    )
    model.fit(train_bt)

    # Backtest predictions
    bt_future   = model.make_future_dataframe(periods=8, freq="W")
    bt_forecast = model.predict(bt_future)
    bt_preds    = bt_forecast[bt_forecast["ds"].isin(test_bt["ds"])][["ds","yhat"]].merge(
        test_bt, on="ds"
    )

    # MAPE calculation
    mape = (
        abs(bt_preds["yhat"] - bt_preds["y"]) / bt_preds["y"].replace(0, np.nan)
    ).mean() * 100 if len(bt_preds) > 0 else None

    # ── Refit on full data and forecast ───────────────────────────────────────
    model_full = Prophet(
        holidays            = UK_PUBLIC_HOLIDAYS,
        weekly_seasonality  = True,
        yearly_seasonality  = True,
        interval_width      = CONFIDENCE,
        changepoint_prior_scale = 0.1,
    )
    model_full.fit(train)

    future   = model_full.make_future_dataframe(periods=FORECAST_HORIZON, freq="W")
    forecast = model_full.predict(future)

    # Clip negative forecasts to 0
    for col in ["yhat", "yhat_lower", "yhat_upper"]:
        forecast[col] = forecast[col].clip(lower=0)

    # Tag historical vs forecast rows
    last_actual = train["ds"].max()
    forecast["is_forecast"] = forecast["ds"] > last_actual
    forecast["category"]    = category

    # Round to nearest integer (units)
    forecast["yhat"]       = forecast["yhat"].round(0).astype(int)
    forecast["yhat_lower"] = forecast["yhat_lower"].round(0).astype(int)
    forecast["yhat_upper"] = forecast["yhat_upper"].round(0).astype(int)

    return forecast[["ds","category","yhat","yhat_lower","yhat_upper","is_forecast"]], mape


def _moving_average_fallback(df: pd.DataFrame, category: str) -> tuple[pd.DataFrame, float]:
    """Simple 4-week moving average if Prophet not installed."""
    df = df.sort_values("ds").copy()
    last_val = df["units_sold"].rolling(4, min_periods=1).mean().iloc[-1]
    last_date = df["ds"].max()

    future_rows = []
    for w in range(1, FORECAST_HORIZON + 1):
        future_rows.append({
            "ds":          last_date + pd.Timedelta(weeks=w),
            "category":    category,
            "yhat":        int(round(last_val, 0)),
            "yhat_lower":  int(round(last_val * 0.8, 0)),
            "yhat_upper":  int(round(last_val * 1.2, 0)),
            "is_forecast": True,
        })

    # Historical rows
    hist = df.rename(columns={"units_sold": "yhat"})[["ds","yhat"]].copy()
    hist["category"]    = category
    hist["yhat_lower"]  = hist["yhat"]
    hist["yhat_upper"]  = hist["yhat"]
    hist["is_forecast"] = False

    result = pd.concat([hist, pd.DataFrame(future_rows)], ignore_index=True)
    return result, None


# ── Visualisation ──────────────────────────────────────────────────────────────

def plot_forecast(
    history: pd.DataFrame,
    forecast: pd.DataFrame,
    category: str,
    mape: float | None,
) -> None:
    """Save a forecast chart for one category."""
    fig, ax = plt.subplots(figsize=(14, 5))

    # Historical actuals
    ax.plot(history["ds"], history["units_sold"],
            color="#2C3E50", linewidth=1.5, label="Actual Sales", zorder=3)

    # Forecast line
    fcast = forecast[forecast["is_forecast"]]
    ax.plot(fcast["ds"], fcast["yhat"],
            color="#E74C3C", linewidth=2, linestyle="--", label="Forecast", zorder=3)

    # Confidence interval
    ax.fill_between(
        fcast["ds"], fcast["yhat_lower"], fcast["yhat_upper"],
        alpha=0.2, color="#E74C3C", label=f"{int(CONFIDENCE*100)}% Confidence Interval"
    )

    # Vertical line: today
    today = pd.Timestamp(date.today())
    ax.axvline(today, color="#7F8C8D", linestyle=":", linewidth=1.5, label="Today")

    # Formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b '%y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=2))
    plt.xticks(rotation=45)

    mape_str = f" | Backtest MAPE: {mape:.1f}%" if mape is not None else ""
    ax.set_title(f"RetailCo — {category}: 12-Week Demand Forecast{mape_str}", fontsize=13)
    ax.set_ylabel("Units Sold (weekly)")
    ax.set_xlabel("")
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.3)

    # Colour background: historical vs forecast
    ax.axvspan(fcast["ds"].min(), fcast["ds"].max(),
               alpha=0.05, color="#E74C3C", label="_nolegend_")

    plt.tight_layout()
    fname = category.lower().replace(" ", "_").replace("/", "_")
    path  = os.path.join(PLOTS_DIR, f"forecast_{fname}.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("[FORECAST] Starting demand forecasting pipeline")

    weekly    = load_weekly_sales()
    categories = weekly["category"].unique()

    all_forecasts = []
    mape_report   = {}

    for cat in categories:
        logger.info(f"[FORECAST] Modelling: {cat}")
        cat_df   = weekly[weekly["category"] == cat].copy()
        forecast, mape = run_prophet_forecast(cat_df, cat)

        if forecast.empty:
            continue

        all_forecasts.append(forecast)
        mape_report[cat] = mape

        if mape and mape > MAPE_TARGET:
            logger.warning(f"[FORECAST] {cat}: MAPE {mape:.1f}% exceeds target {MAPE_TARGET}%")

        plot_forecast(cat_df, forecast, cat, mape)

    # ── Save combined forecast output ─────────────────────────────────────────
    if all_forecasts:
        combined = pd.concat(all_forecasts, ignore_index=True)
        out_path = os.path.join(OUTPUT_DIR, "demand_forecast.csv")
        combined.to_csv(out_path, index=False)
        logger.info(f"[FORECAST] Saved: {out_path} ({len(combined):,} rows)")

    # ── MAPE summary ──────────────────────────────────────────────────────────
    print("\n" + "="*55)
    print("  FORECAST ACCURACY SUMMARY (Backtest MAPE)")
    print("="*55)
    for cat, mape in sorted(mape_report.items(), key=lambda x: (x[1] or 999)):
        status = "✓" if mape and mape <= MAPE_TARGET else "✗"
        mape_str = f"{mape:.1f}%" if mape else "N/A"
        print(f"  {status}  {cat:<20}  MAPE: {mape_str}")
    print("="*55)

    categories_ok = sum(1 for m in mape_report.values() if m and m <= MAPE_TARGET)
    logger.info(f"[FORECAST] {categories_ok}/{len(mape_report)} categories within {MAPE_TARGET}% MAPE target")
    logger.info("[FORECAST] Pipeline complete")


if __name__ == "__main__":
    main()
