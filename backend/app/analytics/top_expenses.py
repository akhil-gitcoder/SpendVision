"""Largest transactions for a given period."""
from sqlalchemy.orm import Session

from app.analytics.data import transactions_dataframe


def compute_top_expenses(db: Session, user_id, month: str | None = None, limit: int = 5) -> dict:
    df = transactions_dataframe(db, user_id)
    expenses = df[df["transaction_type"] == "expense"] if not df.empty else df
    if month and not expenses.empty:
        expenses = expenses[expenses["month"] == month]

    if expenses.empty:
        return {"items": []}

    top = expenses.sort_values("amount", ascending=False).head(limit)
    items = [
        {
            "id": row["id"],
            "transaction_date": row["transaction_date"].date().isoformat(),
            "description": row["description"],
            "merchant": row["merchant"],
            "category": row["category"],
            "amount": round(float(row["amount"]), 2),
        }
        for _, row in top.iterrows()
    ]
    return {"items": items}
