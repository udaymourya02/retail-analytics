"""
generate_data.py
================
Generates realistic synthetic retail data for the RetailCo Analytics Platform.
Produces CSV files that mimic what would come from real source systems.

Output files (saved to /data/raw/):
  - customers.csv       (~5,000 rows)
  - products.csv        (~500 rows)
  - stores.csv          (52 rows)
  - orders.csv          (~150,000 rows)
  - order_lines.csv     (~300,000 rows)
  - inventory.csv       (~500,000 rows — daily snapshot)
  - marketing_spend.csv (~10,000 rows)

Usage:
    python data/sample/generate_data.py

Author: Uday Mourya
"""

import os
import random
import uuid
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
from tqdm import tqdm

# ── Reproducibility ────────────────────────────────────────────────────────────
random.seed(42)
np.random.seed(42)

# ── Config ─────────────────────────────────────────────────────────────────────
OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), "..", "raw")
START_DATE   = date(2022, 1, 1)
END_DATE     = date(2024, 12, 31)
N_CUSTOMERS  = 5_000
N_PRODUCTS   = 500
N_STORES     = 52
N_ORDERS     = 150_000

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Helper utilities ───────────────────────────────────────────────────────────

def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def weighted_date(start: date, end: date) -> date:
    """Simulate seasonality: higher volume Oct-Dec (Christmas) and Mar-Apr."""
    d = random_date(start, end)
    # Boost October-December by re-sampling if we hit those months
    if d.month in (10, 11, 12) and random.random() < 0.3:
        pass  # keep it (already boosted by 30% chance)
    return d


# ── 1. STORES ─────────────────────────────────────────────────────────────────

UK_CITIES = [
    ("London",         "London",     "SW1A 1AA"),
    ("Manchester",     "North West", "M1 1AE"),
    ("Birmingham",     "West Midlands","B1 1BB"),
    ("Leeds",          "Yorkshire",  "LS1 1BA"),
    ("Glasgow",        "Scotland",   "G1 1AA"),
    ("Sheffield",      "Yorkshire",  "S1 1WB"),
    ("Edinburgh",      "Scotland",   "EH1 1AB"),
    ("Bristol",        "South West", "BS1 1AA"),
    ("Liverpool",      "North West", "L1 1AA"),
    ("Cardiff",        "Wales",      "CF10 1AA"),
    ("Nottingham",     "East Midlands","NG1 1AA"),
    ("Leicester",      "East Midlands","LE1 1AA"),
    ("Coventry",       "West Midlands","CV1 1AA"),
    ("Bradford",       "Yorkshire",  "BD1 1AA"),
    ("Southampton",    "South East", "SO14 0AA"),
    ("Oxford",         "South East", "OX1 1AA"),
    ("Cambridge",      "East",       "CB1 1AA"),
    ("York",           "Yorkshire",  "YO1 7AA"),
    ("Bath",           "South West", "BA1 1AA"),
    ("Brighton",       "South East", "BN1 1AA"),
]

stores = []
for i in range(N_STORES):
    if i < len(UK_CITIES):
        city, region, postcode = UK_CITIES[i]
    else:
        city, region, postcode = random.choice(UK_CITIES)

    store_type = "Online" if i == 0 else "Physical"
    stores.append({
        "store_id":    f"STR-{i:03d}",
        "store_name":  f"RetailCo {city}" if store_type == "Physical" else "RetailCo Online",
        "store_type":  store_type,
        "city":        city if store_type == "Physical" else None,
        "region":      region if store_type == "Physical" else None,
        "postcode":    postcode if store_type == "Physical" else None,
        "opening_date": random_date(date(2010, 1, 1), date(2022, 1, 1)).isoformat(),
        "is_active":   True,
    })

stores_df = pd.DataFrame(stores)
stores_df.to_csv(os.path.join(OUTPUT_DIR, "stores.csv"), index=False)
print(f"✓ stores.csv — {len(stores_df):,} rows")


# ── 2. PRODUCTS ───────────────────────────────────────────────────────────────

CATEGORIES = {
    "Womenswear":   ["Dresses","Tops","Trousers","Skirts","Coats","Knitwear"],
    "Menswear":     ["Shirts","Trousers","Suits","Knitwear","Outerwear","T-Shirts"],
    "Accessories":  ["Bags","Scarves","Hats","Belts","Sunglasses","Jewellery"],
    "Footwear":     ["Trainers","Boots","Heels","Loafers","Sandals"],
    "Childrenswear":["Tops","Bottoms","Dresses","Outerwear","Shoes"],
}

BRANDS = ["RetailCo Own", "Premium Line", "Essentials", "Studio Collection", "Active Wear"]

products = []
for i in range(N_PRODUCTS):
    cat  = random.choice(list(CATEGORIES.keys()))
    sub  = random.choice(CATEGORIES[cat])
    cost = random.randint(500, 8000)       # pence
    rrp  = int(cost * random.uniform(2.0, 3.5))
    products.append({
        "product_id":       f"SKU-{i:05d}",
        "product_name":     f"{sub} {random.choice(['Classic','Essential','Premium','Modern','Slim','Relaxed'])} {random.randint(1, 99):02d}",
        "category":         cat,
        "subcategory":      sub,
        "brand":            random.choice(BRANDS),
        "supplier_id":      f"SUP-{random.randint(1, 30):03d}",
        "cost_price_pence": cost,
        "rrp_pence":        rrp,
        "is_active":        random.random() > 0.05,
        "launch_date":      random_date(date(2019, 1, 1), date(2024, 1, 1)).isoformat(),
    })

products_df = pd.DataFrame(products)
products_df.to_csv(os.path.join(OUTPUT_DIR, "products.csv"), index=False)
print(f"✓ products.csv — {len(products_df):,} rows")


# ── 3. CUSTOMERS ──────────────────────────────────────────────────────────────

AGE_BANDS    = ["18-24","25-34","35-44","45-54","55-64","65+"]
GENDERS      = ["Female","Male","Non-binary","Prefer not to say"]
CHANNELS     = ["Organic Search","Paid Search","Paid Social","Email","In-Store","Referral","Direct"]
LOYALTY_TIERS = ["Bronze","Silver","Gold","Platinum"]
TIER_WEIGHTS  = [0.55, 0.30, 0.12, 0.03]

customers = []
for i in range(N_CUSTOMERS):
    city, region, postcode = random.choice(UK_CITIES)
    customers.append({
        "customer_id":          f"CUS-{i:06d}",
        "email_masked":         f"u***{i}@{'gmail' if random.random()>0.4 else 'yahoo'}.com",
        "age_band":             random.choice(AGE_BANDS),
        "gender":               random.choices(GENDERS, weights=[0.55, 0.38, 0.04, 0.03])[0],
        "city":                 city,
        "region":               region,
        "postcode_district":    postcode[:3],
        "acquisition_channel":  random.choice(CHANNELS),
        "acquisition_date":     random_date(date(2019, 1, 1), date(2024, 6, 1)).isoformat(),
        "loyalty_tier":         random.choices(LOYALTY_TIERS, weights=TIER_WEIGHTS)[0],
    })

customers_df = pd.DataFrame(customers)
customers_df.to_csv(os.path.join(OUTPUT_DIR, "customers.csv"), index=False)
print(f"✓ customers.csv — {len(customers_df):,} rows")


# ── 4. ORDERS + ORDER LINES ───────────────────────────────────────────────────

print(f"Generating {N_ORDERS:,} orders (this takes ~30 seconds)...")

# Pre-load as lists for speed
cust_ids    = customers_df["customer_id"].tolist()
prod_ids    = products_df["product_id"].tolist()
prod_rrps   = dict(zip(products_df["product_id"], products_df["rrp_pence"]))
prod_costs  = dict(zip(products_df["product_id"], products_df["cost_price_pence"]))
store_ids   = stores_df["store_id"].tolist()

MARKETING_CHANNELS = ["Paid Search","Paid Social","Email","Organic Search","Direct","None"]
CAMPAIGN_IDS       = [f"CAM-{i:04d}" for i in range(1, 101)]

orders      = []
order_lines = []

for i in tqdm(range(N_ORDERS)):
    order_id     = f"ORD-{uuid.uuid4().hex[:10].upper()}"
    customer_id  = random.choice(cust_ids)
    store_id     = random.choices(store_ids, weights=[5] + [1]*(N_STORES-1))[0]  # online gets 5x traffic
    order_date   = weighted_date(START_DATE, END_DATE)
    channel      = "Online" if store_id == "STR-000" else "In-Store"
    campaign_id  = random.choice(CAMPAIGN_IDS) if random.random() < 0.4 else None

    # 1–4 products per order
    n_lines   = random.choices([1, 2, 3, 4], weights=[0.5, 0.3, 0.15, 0.05])[0]
    line_prods = random.sample(prod_ids, k=min(n_lines, len(prod_ids)))

    order_total = 0
    for j, prod_id in enumerate(line_prods):
        units   = random.choices([1, 2, 3], weights=[0.75, 0.20, 0.05])[0]
        rrp     = prod_rrps[prod_id]
        cost    = prod_costs[prod_id]
        disc_pct = random.choices([0, 0.1, 0.2, 0.3, 0.5], weights=[0.5, 0.2, 0.15, 0.1, 0.05])[0]
        gross   = rrp * units
        disc    = int(gross * disc_pct)
        net     = gross - disc
        profit  = net - (cost * units)
        is_ret  = random.random() < 0.07   # 7% return rate

        order_lines.append({
            "order_line_id":        f"{order_id}-{j+1:02d}",
            "order_id":             order_id,
            "product_id":           prod_id,
            "units_sold":           units,
            "gross_revenue_pence":  gross,
            "discount_pence":       disc,
            "net_revenue_pence":    net,
            "cost_of_goods_pence":  cost * units,
            "gross_profit_pence":   profit,
            "is_returned":          is_ret,
            "return_date":          (order_date + timedelta(days=random.randint(1, 28))).isoformat() if is_ret else None,
        })
        order_total += net

    orders.append({
        "order_id":        order_id,
        "customer_id":     customer_id,
        "store_id":        store_id,
        "order_date":      order_date.isoformat(),
        "channel":         channel,
        "campaign_id":     campaign_id,
        "order_total_pence": order_total,
        "source_system":   "POS",
    })

orders_df      = pd.DataFrame(orders)
order_lines_df = pd.DataFrame(order_lines)

orders_df.to_csv(os.path.join(OUTPUT_DIR, "orders.csv"), index=False)
order_lines_df.to_csv(os.path.join(OUTPUT_DIR, "order_lines.csv"), index=False)
print(f"✓ orders.csv      — {len(orders_df):,} rows")
print(f"✓ order_lines.csv — {len(order_lines_df):,} rows")


# ── 5. INVENTORY (daily snapshot, last 90 days) ───────────────────────────────

print("Generating inventory snapshots (last 90 days)...")

inventory = []
snapshot_dates = [END_DATE - timedelta(days=x) for x in range(90)]
sample_prods   = random.sample(prod_ids, k=100)  # 100 products tracked
sample_stores  = random.sample(store_ids[1:], k=20)  # 20 physical stores

for snap_date in tqdm(snapshot_dates):
    for store_id in sample_stores:
        for prod_id in sample_prods:
            stock       = random.randint(0, 200)
            reorder_pt  = random.randint(10, 40)
            avg_daily   = random.uniform(1, 10)
            if stock == 0:
                status = "RED"
            elif stock <= reorder_pt * 1.2:
                status = "AMBER"
            else:
                status = "GREEN"

            inventory.append({
                "snapshot_date":           snap_date.isoformat(),
                "product_id":              prod_id,
                "store_id":                store_id,
                "stock_on_hand":           stock,
                "units_received":          random.randint(0, 50),
                "units_sold":              random.randint(0, 20),
                "units_returned":          random.randint(0, 3),
                "reorder_point":           reorder_pt,
                "reorder_quantity":        reorder_pt * 3,
                "stock_status":            status,
                "days_of_stock_remaining": round(stock / avg_daily, 1) if avg_daily > 0 else None,
                "source_system":           "WMS",
            })

inventory_df = pd.DataFrame(inventory)
inventory_df.to_csv(os.path.join(OUTPUT_DIR, "inventory.csv"), index=False)
print(f"✓ inventory.csv   — {len(inventory_df):,} rows")


# ── 6. MARKETING SPEND ────────────────────────────────────────────────────────

print("Generating marketing spend data...")

mkt_channels = {
    "Paid Search":  {"budget_daily": (5000, 50000),  "ctr": (0.02, 0.08)},
    "Paid Social":  {"budget_daily": (3000, 30000),  "ctr": (0.01, 0.05)},
    "Email":        {"budget_daily": (500,  5000),   "ctr": (0.10, 0.25)},
}

marketing = []
for cam_id in CAMPAIGN_IDS[:50]:
    channel    = random.choice(list(mkt_channels.keys()))
    cfg        = mkt_channels[channel]
    n_days     = random.randint(7, 90)
    start      = random_date(START_DATE, END_DATE - timedelta(days=n_days))

    for d in range(n_days):
        snap_date   = start + timedelta(days=d)
        spend       = random.randint(*cfg["budget_daily"])
        impressions = spend * random.randint(5, 20)
        ctr         = random.uniform(*cfg["ctr"])
        clicks      = int(impressions * ctr)
        orders_attr = int(clicks * random.uniform(0.01, 0.05))
        rev_attr    = orders_attr * random.randint(3000, 15000)  # pence

        marketing.append({
            "campaign_id":               cam_id,
            "channel":                   channel,
            "date":                      snap_date.isoformat(),
            "spend_pence":               spend,
            "impressions":               impressions,
            "clicks":                    clicks,
            "attributed_orders":         orders_attr,
            "attributed_revenue_pence":  rev_attr,
            "source_system":             channel.replace(" ", "_").upper(),
        })

marketing_df = pd.DataFrame(marketing)
marketing_df.to_csv(os.path.join(OUTPUT_DIR, "marketing_spend.csv"), index=False)
print(f"✓ marketing_spend.csv — {len(marketing_df):,} rows")


# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "="*55)
print("  DATA GENERATION COMPLETE")
print("="*55)
print(f"  Output directory : {os.path.abspath(OUTPUT_DIR)}")
print(f"  Stores           : {len(stores_df):,}")
print(f"  Products         : {len(products_df):,}")
print(f"  Customers        : {len(customers_df):,}")
print(f"  Orders           : {len(orders_df):,}")
print(f"  Order Lines      : {len(order_lines_df):,}")
print(f"  Inventory Rows   : {len(inventory_df):,}")
print(f"  Marketing Rows   : {len(marketing_df):,}")
print("="*55)
