"""Generate mock corporate orders for MetricMind (stdlib only).

Writes dbt/seeds/raw_orders.csv covering the last 5 complete calendar quarters
plus the current quarter so far.

Planted story (so the demo question has a real answer):
  In the LAST COMPLETE QUARTER, Europe shifts most shipments from Sea/Road to
  Air freight (and pays an air surcharge). Shipping cost per order jumps and
  Europe's gross margin drops. Other regions stay stable.

Ask MetricMind: "Why did our European margins drop last quarter?"
"""
import csv
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

random.seed(42)
OUT = Path(__file__).resolve().parents[1] / "dbt" / "seeds" / "raw_orders.csv"

REGIONS = {
    "Europe": dict(weight=0.32, ship=1.0, countries=["Germany", "France", "United Kingdom", "Italy", "Spain", "Netherlands"]),
    "North America": dict(weight=0.34, ship=1.1, countries=["United States", "Canada", "Mexico"]),
    "APAC": dict(weight=0.24, ship=1.3, countries=["Japan", "Australia", "India", "Singapore"]),
    "LATAM": dict(weight=0.10, ship=1.4, countries=["Brazil", "Argentina", "Chile"]),
}
CATEGORIES = {  # price range, material cost ratio, freight weight factor, order share
    "Laptops": dict(price=(750, 1400), material=0.58, weight=2.5, share=0.15),
    "Audio": dict(price=(60, 260), material=0.52, weight=0.8, share=0.25),
    "Wearables": dict(price=(120, 380), material=0.55, weight=0.5, share=0.20),
    "Accessories": dict(price=(20, 90), material=0.45, weight=0.3, share=0.40),
}
SEGMENTS = {  # share, units range, discount range
    "Enterprise": dict(share=0.25, units=(5, 40), disc=(0.08, 0.18)),
    "SMB": dict(share=0.45, units=(2, 12), disc=(0.03, 0.10)),
    "Consumer": dict(share=0.30, units=(1, 3), disc=(0.00, 0.05)),
}
SHIP_PER_UNIT = {"Sea": 4.0, "Road": 7.0, "Air": 22.0}
NORMAL_MODES = {"Sea": 0.45, "Road": 0.45, "Air": 0.10}
ANOMALY_MODES = {"Sea": 0.20, "Road": 0.30, "Air": 0.50}


def add_months(d: date, n: int) -> date:
    y, m = divmod(d.year * 12 + d.month - 1 + n, 12)
    return date(y, m + 1, 1)


def quarter_start(d: date) -> date:
    return date(d.year, 3 * ((d.month - 1) // 3) + 1, 1)


def pick(weights: dict):
    return random.choices(list(weights), weights=[v if isinstance(v, (int, float)) else v["share"] for v in weights.values()])[0]


def main() -> None:
    today = date.today()
    cur_q = quarter_start(today)
    last_q_start, last_q_end = add_months(cur_q, -3), cur_q - timedelta(days=1)
    start, end = add_months(cur_q, -15), today - timedelta(days=1)

    rows, totals, n = [], defaultdict(lambda: [0.0, 0.0]), 0
    day = start
    while day <= end:
        base = 26 * (0.6 if day.weekday() >= 5 else 1.0) * (1 + 0.0004 * (day - start).days)
        for _ in range(max(1, int(random.gauss(base, 4)))):
            region = pick({k: v["weight"] for k, v in REGIONS.items()})
            r = REGIONS[region]
            cat_name = pick({k: v["share"] for k, v in CATEGORIES.items()})
            cat = CATEGORIES[cat_name]
            seg_name = pick({k: v["share"] for k, v in SEGMENTS.items()})
            seg = SEGMENTS[seg_name]
            anomaly = region == "Europe" and last_q_start <= day <= last_q_end
            mode = pick(ANOMALY_MODES if anomaly else NORMAL_MODES)
            units = random.randint(*seg["units"])
            price = round(random.uniform(*cat["price"]), 2)
            disc = round(random.uniform(*seg["disc"]), 4)
            revenue = units * price * (1 - disc)
            material = units * price * cat["material"] * random.uniform(0.97, 1.03) * (1.02 if anomaly else 1.0)
            shipping = units * SHIP_PER_UNIT[mode] * cat["weight"] * r["ship"] * random.uniform(0.9, 1.1) * (1.25 if anomaly and mode == "Air" else 1.0)
            n += 1
            rows.append([
                f"ORD-{n:06d}", day.isoformat(), region, random.choice(r["countries"]), cat_name,
                seg_name, mode, units, price, disc, round(material, 2), round(shipping, 2),
            ])
            q = f"{day.year} Q{(day.month - 1) // 3 + 1}"
            totals[(region, q)][0] += revenue
            totals[(region, q)][1] += material + shipping
        day += timedelta(days=1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "order_date", "region", "country", "product_category", "customer_segment",
                    "shipping_mode", "units", "unit_price", "discount_pct", "material_cost", "shipping_cost"])
        w.writerows(rows)

    print(f"Wrote {len(rows):,} orders to {OUT}")
    print("\nGross margin % by region and quarter (sanity check):")
    quarters = sorted({q for _, q in totals})
    print(f"{'':16}" + "".join(f"{q:>10}" for q in quarters))
    for region in REGIONS:
        cells = "".join(
            f"{100 * (1 - totals[(region, q)][1] / totals[(region, q)][0]):>9.1f}%" if totals[(region, q)][0] else f"{'-':>10}"
            for q in quarters
        )
        print(f"{region:16}{cells}")


if __name__ == "__main__":
    main()
