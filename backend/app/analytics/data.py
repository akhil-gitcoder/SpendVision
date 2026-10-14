"""Shared data-loading helper: pulls a user's transactions into a pandas
DataFrame so the rest of the analytics module can use vectorized pandas
operations instead of hand-rolled loops."""
from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Transaction


def transactions_dataframe(
    db: Session,
    user_id,
    start: date | None = None,
    end: date | None = None,
) -> pd.DataFrame:
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if start is not None:
        query = query.filter(Transaction.transaction_date >= start)
    if end is not None:
        query = query.filter(Transaction.transaction_date <= end)

    rows = query.all()
    if not rows:
        return pd.DataFrame(
            columns=["id", "transaction_date", "description", "merchant", "amount", "transaction_type", "category"]
        )

    data = [
        {
            "id": str(t.id),
            "transaction_date": pd.Timestamp(t.transaction_date),
            "description": t.description,
            "merchant": t.merchant,
            "amount": float(t.amount),
            "transaction_type": t.transaction_type.value,
            "category": t.category.name if t.category else "Uncategorized",
        }
        for t in rows
    ]
    df = pd.DataFrame(data)
    df["month"] = df["transaction_date"].dt.strftime("%Y-%m")
    return df
