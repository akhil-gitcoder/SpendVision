"""
Assembles the bounded, structured statistics package that gets handed to
the AI insights layer (app/ai/insights.py). This is the deterministic half
of the "deterministic calculation vs AI interpretation" split described in
the project README: every number here comes straight from SQL/pandas, none
of it is guessed by an LLM.
"""
from sqlalchemy.orm import Session

from app.analytics.comparison import compute_month_comparison
from app.analytics.summary import compute_summary
from app.analytics.top_expenses import compute_top_expenses
from app.analytics.trends import compute_category_breakdown
from app.utils.dates import current_month, month_bounds


def build_insight_stats(db: Session, user_id, month: str | None = None) -> dict:
    if month is None:
        month = current_month()

    comparison = compute_month_comparison(db, user_id, month)
    breakdown = compute_category_breakdown(db, user_id, month)
    top = compute_top_expenses(db, user_id, month, limit=3)
    start, end = month_bounds(month)
    summary = compute_summary(db, user_id, start, end)

    # Only include categories that actually moved, and cap the list, so the
    # prompt sent to the LLM stays small and relevant (context limitation).
    notable_changes = [
        c
        for c in comparison["category_changes"]
        if c["current_amount"] > 0 or c["previous_amount"] > 0
    ][:8]

    return {
        "month": month,
        "current_month_expenses": comparison["current_total"],
        "previous_month_expenses": comparison["previous_total"],
        "change_percent": comparison["change_percent"],
        "category_breakdown": {item["category"]: item["amount"] for item in breakdown["items"]},
        "category_changes": notable_changes,
        "top_expenses": top["items"],
        "total_income": summary["total_income"],
        "total_savings": summary["total_savings"],
        "savings_rate": summary["savings_rate"],
        "transaction_count": summary["transaction_count"],
    }
