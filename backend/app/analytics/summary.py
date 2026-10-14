"""Summary card figures: total income, expenses, savings, savings rate."""
from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.data import transactions_dataframe


def compute_summary(db: Session, user_id, start: date | None = None, end: date | None = None) -> dict:
    df = transactions_dataframe(db, user_id, start, end)

    if df.empty:
        return {
            "total_income": 0.0,
            "total_expenses": 0.0,
            "total_savings": 0.0,
            "savings_rate": 0.0,
            "period_start": start.isoformat() if start else None,
            "period_end": end.isoformat() if end else None,
            "transaction_count": 0,
        }

    total_income = float(df.loc[df["transaction_type"] == "income", "amount"].sum())
    total_expenses = float(df.loc[df["transaction_type"] == "expense", "amount"].sum())
    total_savings = total_income - total_expenses
    savings_rate = (total_savings / total_income * 100) if total_income > 0 else 0.0

    period_start = start.isoformat() if start else df["transaction_date"].min().date().isoformat()
    period_end = end.isoformat() if end else df["transaction_date"].max().date().isoformat()

    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "total_savings": round(total_savings, 2),
        "savings_rate": round(savings_rate, 2),
        "period_start": period_start,
        "period_end": period_end,
        "transaction_count": int(len(df)),
    }
