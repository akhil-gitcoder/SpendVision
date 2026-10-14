"""Spending trend over time (daily/weekly/monthly) and category breakdown."""
import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.data import transactions_dataframe

VALID_GRANULARITIES = {"daily", "weekly", "monthly"}


def compute_monthly_trend(db: Session, user_id, granularity: str = "monthly") -> dict:
    if granularity not in VALID_GRANULARITIES:
        granularity = "monthly"

    df = transactions_dataframe(db, user_id)
    if df.empty:
        return {"granularity": granularity, "points": []}

    freq_map = {"daily": "D", "weekly": "W", "monthly": "MS"}
    fmt_map = {"daily": "%Y-%m-%d", "weekly": "%Y-%m-%d", "monthly": "%Y-%m"}

    df = df.set_index("transaction_date")
    grouped = df.groupby([pd.Grouper(freq=freq_map[granularity]), "transaction_type"])["amount"].sum()
    grouped = grouped.unstack(fill_value=0.0)

    for col in ("income", "expense"):
        if col not in grouped.columns:
            grouped[col] = 0.0

    points = [
        {
            "period": idx.strftime(fmt_map[granularity]),
            "income": round(float(row["income"]), 2),
            "expenses": round(float(row["expense"]), 2),
        }
        for idx, row in grouped.iterrows()
    ]

    return {"granularity": granularity, "points": points}


def compute_category_breakdown(db: Session, user_id, month: str | None = None) -> dict:
    df = transactions_dataframe(db, user_id)
    if not df.empty and month:
        df = df[df["month"] == month]

    expenses = df[df["transaction_type"] == "expense"] if not df.empty else df
    total = float(expenses["amount"].sum()) if not expenses.empty else 0.0

    if total == 0.0:
        return {"total_expenses": 0.0, "items": []}

    grouped = expenses.groupby("category")["amount"].sum().sort_values(ascending=False)
    items = [
        {"category": cat, "amount": round(float(amt), 2), "percent": round(float(amt) / total * 100, 2)}
        for cat, amt in grouped.items()
    ]
    return {"total_expenses": round(total, 2), "items": items}
