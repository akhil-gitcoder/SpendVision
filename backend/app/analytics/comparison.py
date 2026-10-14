"""Month-over-month comparison, overall and by category."""
from sqlalchemy.orm import Session

from app.analytics.data import transactions_dataframe
from app.utils.dates import current_month, previous_month as _previous_month


def _pct_change(current: float, previous: float) -> float | None:
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 2)


def compute_month_comparison(db: Session, user_id, month: str | None = None) -> dict:
    if month is None:
        month = current_month()
    previous_month_str = _previous_month(month)

    df = transactions_dataframe(db, user_id)
    expenses = df[df["transaction_type"] == "expense"] if not df.empty else df

    current_df = expenses[expenses["month"] == month] if not expenses.empty else expenses
    previous_df = expenses[expenses["month"] == previous_month_str] if not expenses.empty else expenses

    current_total = float(current_df["amount"].sum()) if not current_df.empty else 0.0
    previous_total = float(previous_df["amount"].sum()) if not previous_df.empty else 0.0

    current_by_cat = current_df.groupby("category")["amount"].sum() if not current_df.empty else {}
    previous_by_cat = previous_df.groupby("category")["amount"].sum() if not previous_df.empty else {}

    all_categories = set(getattr(current_by_cat, "index", [])) | set(getattr(previous_by_cat, "index", []))
    category_changes = []
    for cat in sorted(all_categories):
        cur = float(current_by_cat.get(cat, 0.0)) if len(current_by_cat) else 0.0
        prev = float(previous_by_cat.get(cat, 0.0)) if len(previous_by_cat) else 0.0
        category_changes.append(
            {
                "category": cat,
                "current_amount": round(cur, 2),
                "previous_amount": round(prev, 2),
                "change_percent": _pct_change(cur, prev),
            }
        )
    category_changes.sort(key=lambda c: c["current_amount"], reverse=True)

    return {
        "current_month": month,
        "previous_month": previous_month_str,
        "current_total": round(current_total, 2),
        "previous_total": round(previous_total, 2),
        "change_percent": _pct_change(current_total, previous_total),
        "category_changes": category_changes,
    }
