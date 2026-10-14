"""
AI-generated spending insights.

The backend (app/services/insights_data.py) has already computed every
number involved. This module's only job is to turn those numbers into
short, readable observations - it must not invent figures. When no LLM is
configured, `_template_insights` produces the same kind of output using
plain conditional logic, so the Insights page always has something useful
to show.
"""
import json
import logging

from app.ai.provider import LLMProvider, AIProviderError
from app.ai.text import clean_ai_text
from app.ai.prompts import INSIGHTS_SYSTEM_PROMPT, build_insights_user_prompt

logger = logging.getLogger(__name__)

ALLOWED_SEVERITIES = {"info", "positive", "warning"}
SIGNIFICANT_CHANGE_PCT = 15.0


def _template_insights(stats: dict) -> list[dict]:
    insights: list[dict] = []

    change_pct = stats.get("change_percent")
    current = stats.get("current_month_expenses", 0)
    previous = stats.get("previous_month_expenses", 0)
    if change_pct is not None:
        direction = "increased" if change_pct > 0 else "decreased"
        severity = "warning" if change_pct > SIGNIFICANT_CHANGE_PCT else "info"
        insights.append(
            {
                "title": f"Spending {direction} this month",
                "detail": (
                    f"Total expenses {direction} {abs(change_pct):.1f}% compared to last month "
                    f"(₹{current:,.0f} vs ₹{previous:,.0f})."
                ),
                "severity": severity,
            }
        )
    elif current > 0:
        insights.append(
            {
                "title": "Spending this month",
                "detail": f"You've spent ₹{current:,.0f} so far this month.",
                "severity": "info",
            }
        )

    breakdown = stats.get("category_breakdown", {})
    if breakdown:
        top_category = max(breakdown, key=breakdown.get)
        insights.append(
            {
                "title": f"{top_category} is your top category",
                "detail": (
                    f"{top_category} accounts for ₹{breakdown[top_category]:,.0f} of this month's spending, "
                    "your largest single category."
                ),
                "severity": "info",
            }
        )

    changes = [c for c in stats.get("category_changes", []) if c.get("change_percent") is not None]
    if changes:
        biggest = max(changes, key=lambda c: abs(c["change_percent"]))
        if abs(biggest["change_percent"]) >= SIGNIFICANT_CHANGE_PCT:
            direction = "up" if biggest["change_percent"] > 0 else "down"
            insights.append(
                {
                    "title": f"{biggest['category']} spending shifted",
                    "detail": (
                        f"{biggest['category']} is {direction} {abs(biggest['change_percent']):.1f}% "
                        f"versus last month (₹{biggest['previous_amount']:,.0f} → ₹{biggest['current_amount']:,.0f})."
                    ),
                    "severity": "warning" if direction == "up" else "positive",
                }
            )

    savings_rate = stats.get("savings_rate")
    if savings_rate is not None and stats.get("total_income", 0) > 0:
        severity = "positive" if savings_rate >= 20 else ("warning" if savings_rate < 0 else "info")
        insights.append(
            {
                "title": "Savings rate",
                "detail": f"You saved {savings_rate:.1f}% of your income this month.",
                "severity": severity,
            }
        )

    return insights[:5] if insights else [
        {
            "title": "Not enough data yet",
            "detail": "Upload more transactions to start seeing spending insights.",
            "severity": "info",
        }
    ]


def _validate_ai_insights(raw_items) -> list[dict] | None:
    if not isinstance(raw_items, list) or not raw_items:
        return None

    validated = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        title, detail, severity = item.get("title"), item.get("detail"), item.get("severity")
        if not isinstance(title, str) or not isinstance(detail, str):
            continue
        if severity not in ALLOWED_SEVERITIES:
            severity = "info"
        validated.append({"title": clean_ai_text(title)[:80], "detail": clean_ai_text(detail)[:400], "severity": severity})

    return validated[:5] if validated else None


def generate_insights(provider: LLMProvider | None, stats: dict) -> tuple[list[dict], bool]:
    """Returns (insights, ai_available). Falls back to template insights on
    any provider/parsing failure - insights should never 500 the request."""
    if provider is None:
        return _template_insights(stats), False

    try:
        raw = provider.generate(
            INSIGHTS_SYSTEM_PROMPT,
            build_insights_user_prompt(stats),
            max_tokens=600,
        )
        parsed = json.loads(raw)
        validated = _validate_ai_insights(parsed)
        if validated is not None:
            return validated, True
        logger.warning("AI insights response failed validation, using template fallback")
    except (AIProviderError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("AI insights generation failed, using template fallback: %s", exc)

    return _template_insights(stats), False
