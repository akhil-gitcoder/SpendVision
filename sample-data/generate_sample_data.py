"""
One-off generator script for sample_transactions.csv.

Not part of the running application - kept here only so the sample data
can be regenerated or extended later. Produces realistic demo data across
five months with a monthly salary, recurring bills/subscriptions, everyday
spending across all categories, and a handful of deliberately unusual
transactions to exercise the anomaly detector.
"""
import csv
import random
from datetime import date

random.seed(42)

MONTHS = [(2026, 4), (2026, 5), (2026, 6), (2026, 7), (2026, 8)]

# The importer rejects future-dated rows, so the in-progress current month
# is capped at "today" rather than running through the full month.
TODAY = date(2026, 8, 18)


def day_max(year: int, month: int) -> int:
    if (year, month) == (TODAY.year, TODAY.month):
        return TODAY.day
    return 28


def rand_day(dm: int, low: int = 1, high: int = 28) -> int:
    lo, hi = min(low, dm), min(high, dm)
    if lo > hi:
        lo = hi
    return random.randint(lo, hi)


FOOD = ["Swiggy", "Zomato", "Dominos", "Starbucks", "Cafe Coffee Day", "McDonald's", "Chai Point"]
GROCERIES = ["DMart", "BigBasket", "Blinkit", "Zepto", "Reliance Fresh"]
TRANSPORT = ["Uber", "Ola", "Indian Oil Petrol Pump", "IRCTC", "Metro Card Recharge"]
SHOPPING = ["Amazon", "Flipkart", "Myntra", "Ajio", "Nykaa"]
ENTERTAINMENT = ["Netflix", "Spotify", "Amazon Prime Video", "BookMyShow", "PVR Cinemas", "Hotstar"]
UTILITIES = ["Electricity Board", "Airtel Broadband", "Jio Recharge", "Water Bill", "Gas Bill"]
HEALTHCARE = ["Apollo Pharmacy", "PharmEasy", "Practo Consultation"]
EDUCATION = ["Udemy", "Coursera"]

rows = []


def add(d: date, description: str, amount: float, txn_type: str):
    rows.append({"date": d.isoformat(), "description": description, "amount": round(amount, 2), "type": txn_type})


for (year, month) in MONTHS:
    dm = day_max(year, month)

    # Income: salary on the 1st, always
    add(date(year, month, 1), "Salary", 65000, "income")

    # Rent, always on the 3rd (or day_max if the month hasn't reached the 3rd yet)
    add(date(year, month, min(3, dm)), "Rent", 15000, "expense")

    # Utilities - a handful of recurring bills each month
    for merchant, amt in [
        ("Electricity Board", random.uniform(900, 1600)),
        ("Airtel Broadband", 799),
        ("Jio Recharge", random.choice([299, 399, 719])),
        ("Water Bill", random.uniform(250, 450)),
    ]:
        add(date(year, month, rand_day(dm, 4, 10)), merchant, amt, "expense")

    # Entertainment subscriptions
    add(date(year, month, min(5, dm)), "Netflix", 649, "expense")
    add(date(year, month, min(6, dm)), "Spotify", 119, "expense")

    # Groceries - a few trips per month
    for _ in range(random.randint(3, 5)):
        add(date(year, month, rand_day(dm)), random.choice(GROCERIES), random.uniform(400, 2200), "expense")

    # Food delivery / dining out - frequent, smaller amounts
    for _ in range(random.randint(6, 10)):
        add(date(year, month, rand_day(dm)), random.choice(FOOD), random.uniform(150, 900), "expense")

    # Transport
    for _ in range(random.randint(4, 8)):
        add(date(year, month, rand_day(dm)), random.choice(TRANSPORT), random.uniform(80, 500), "expense")

    # Shopping - a couple of purchases
    for _ in range(random.randint(1, 3)):
        add(date(year, month, rand_day(dm)), random.choice(SHOPPING), random.uniform(500, 3500), "expense")

    # Occasional entertainment outing
    if random.random() < 0.7:
        add(date(year, month, rand_day(dm)), random.choice(ENTERTAINMENT), random.uniform(300, 1200), "expense")

    # Healthcare - a couple of routine visits/purchases most months (kept
    # frequent enough that the anomaly detector has real history to compare
    # the deliberate Apollo Pharmacy spike against).
    for _ in range(random.randint(1, 2)):
        add(date(year, month, rand_day(dm)), random.choice(HEALTHCARE), random.uniform(200, 1500), "expense")

    # Education - occasional
    if random.random() < 0.3:
        add(date(year, month, rand_day(dm)), random.choice(EDUCATION), random.uniform(499, 2999), "expense")

    # Occasional investment contribution (income-side, e.g. dividend) - kept rare
    if random.random() < 0.25:
        add(date(year, month, rand_day(dm, 10, 20)), "Zerodha Dividend", random.uniform(500, 2500), "income")

# --- Deliberate anomalies to demonstrate the unusual-spending detector ---
add(date(2026, 6, 14), "Amazon", 18500, "expense")          # Shopping way above typical range
add(date(2026, 7, 22), "Apollo Pharmacy", 9200, "expense")  # Healthcare spike (medical emergency)
add(date(2026, 8, 9), "Flipkart", 22999, "expense")         # Another shopping outlier

rows.sort(key=lambda r: r["date"])

out_path = "sample_transactions.csv"
with open(out_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["date", "description", "amount", "type"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} rows to {out_path}")
