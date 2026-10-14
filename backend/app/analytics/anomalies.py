"""
Lightweight, explainable anomaly detection - deliberately NOT an LLM.

Uses Tukey's IQR ("boxplot") rule per expense category: for each category
with enough history, compute the 25th/75th percentiles (Q1/Q3) of that
category's transaction amounts. A transaction is flagged as unusual if it
falls above the upper fence `Q3 + IQR_MULTIPLIER * (Q3 - Q1)` and clears an
absolute minimum (`MIN_FLAG_AMOUNT`), so tiny categories with tiny variance
don't produce noisy false positives.

The IQR method is used instead of a plain mean/standard-deviation z-score
because it is far more robust to the very outliers it's trying to detect:
a single huge transaction barely moves the median or quartiles, whereas it
can drag a mean and standard deviation up enough to mask itself. Median
and quartiles are simple to compute, don't require external libraries
beyond pandas, and are easy to explain to a user ("this is well above the
middle 50% of your usual X spending").
"""
from sqlalchemy.orm import Session

from app.analytics.data import transactions_dataframe

IQR_MULTIPLIER = 1.5
MIN_SAMPLES = 3
MIN_FLAG_AMOUNT = 1000.0


def detect_anomalies(db: Session, user_id) -> list[dict]:
    df = transactions_dataframe(db, user_id)
    expenses = df[df["transaction_type"] == "expense"] if not df.empty else df
    if expenses.empty:
        return []

    anomalies: list[dict] = []

    for category, group in expenses.groupby("category"):
        if len(group) < MIN_SAMPLES:
            continue

        q1 = float(group["amount"].quantile(0.25))
        q3 = float(group["amount"].quantile(0.75))
        iqr = q3 - q1

        if iqr == 0:
            # No spread in this category's spending - nothing to compare against.
            continue

        upper_fence = q3 + IQR_MULTIPLIER * iqr

        flagged = group[(group["amount"] > upper_fence) & (group["amount"] >= MIN_FLAG_AMOUNT)]
        for _, row in flagged.iterrows():
            anomalies.append(
                {
                    "transaction_id": row["id"],
                    "transaction_date": row["transaction_date"].date().isoformat(),
                    "description": row["description"],
                    "merchant": row["merchant"],
                    "category": category,
                    "amount": round(float(row["amount"]), 2),
                    "typical_range_low": round(q1, 2),
                    "typical_range_high": round(q3, 2),
                    "reason": (
                        f"This {category} transaction (₹{row['amount']:,.0f}) is well above your "
                        f"typical {category} spending of ₹{q1:,.0f}–₹{q3:,.0f}."
                    ),
                }
            )

    anomalies.sort(key=lambda a: a["amount"], reverse=True)
    return anomalies
